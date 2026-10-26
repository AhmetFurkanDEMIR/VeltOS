// SPDX-FileCopyrightText: 2026 VeltOS Developers
// SPDX-License-Identifier: GPL-3.0-or-later
//
// "veltos-installer": the Qt style of the VeltOS installer (Calamares).
//
// It is Kvantum, the live session's style, with Calamares' disk pictures
// drawn in the Windows 11 look of VeltOS. Calamares' partition module paints
// its disk bars, their legend and the "Install alongside" resize bar itself
// (PartitionBarsView, PartitionLabelsView, PartitionSplitterWidget), with
// fixed Breeze colours, black and grey text and sizes such as "300.00 MiB";
// a style sheet cannot reach that painting (product owner, 2026-10-23: the
// disk sizes looked bad). This style takes over those paint events and draws
// the same model at the same places Calamares computes (visualRect, and the
// splitter's own arithmetic), so choosing and resizing partitions works
// exactly as before. Sizes are written as VeltOS Disk Management writes them
// ("40.00 GB", "512 MB"), also in labels and in the disk list.
//
// The partition dialogs (Create a Partition, Edit Partition) get the same
// look: KPMcore's size bar (PartResizerWidget with its PartWidget and two
// handle labels) is drawn as a VeltOS disk bar with a slider thumb, and the
// size box keeps to the space there is. Calamares gives that box no maximum
// (PartitionSizeController::setSpinBox) and only corrects the value when
// editing finishes, so its arrows counted past the free space (product owner,
// 2026-10-26); a step now finishes the edit at once, which makes Calamares
// put the largest possible size back. Nothing else is changed: every other
// call goes to Kvantum (or Qt's default style).

#include <QAbstractItemView>
#include <QComboBox>
#include <QCoreApplication>
#include <QHash>
#include <QIdentityProxyModel>
#include <QKeyEvent>
#include <QLabel>
#include <QLayout>
#include <QLocale>
#include <QMouseEvent>
#include <QPainter>
#include <QPainterPath>
#include <QPersistentModelIndex>
#include <QPointer>
#include <QProxyStyle>
#include <QRadioButton>
#include <QRegularExpression>
#include <QSet>
#include <QSignalBlocker>
#include <QSpinBox>
#include <QStyleFactory>
#include <QStylePlugin>
#include <QStyledItemDelegate>
#include <QTimer>

#include <cmath>
#include <iterator>

namespace
{

// Calamares' PartitionModel (src/modules/partition/core/PartitionModel.h,
// Calamares 3.3) and the kpmcore FileSystem::Type values used here.
enum PartitionRole
{
    SizeRole = Qt::UserRole + 1,
    IsFreeSpaceRole,
    IsPartitionNewRole,
    FileSystemLabelRole,
    FileSystemTypeRole,
    PartitionPathRole,
    PartitionPtrRole,
    OsproberNameRole,
};
enum PartitionColumn
{
    FileSystemColumn = 1,
    MountPointColumn = 3,
};
enum FileSystemType
{
    FsUnknown = 0,
    FsExtended = 1,
    FsLinuxSwap = 5,
    FsUnformatted = 16,
};

// PartitionLabelsView draws its legend this far below the top of the view
// (LAYOUT_MARGIN).
constexpr int LabelsTop = 4;

struct Look
{
    bool dark = false;
    QColor accent { 0x2F, 0x5E, 0xE6 };
    QColor window, card, border, text, subtext, free, hatch;
};

// Light or dark and the accent colour, as start-calamares passes them to the
// installer ("veltos-theme=dark=1;accent=#E81123;software=0").
const Look&
look()
{
    static const Look result = []
    {
        Look l;
        const QStringList arguments = QCoreApplication::arguments();
        for ( const QString& argument : arguments )
        {
            if ( !argument.startsWith( QLatin1String( "veltos-theme=" ) ) )
            {
                continue;
            }
            const QStringList parts = argument.mid( 13 ).split( QLatin1Char( ';' ) );
            for ( const QString& part : parts )
            {
                if ( part == QLatin1String( "dark=1" ) )
                {
                    l.dark = true;
                }
                else if ( part.startsWith( QLatin1String( "accent=" ) ) )
                {
                    const QColor accent = QColor::fromString( part.mid( 7 ) );
                    if ( accent.isValid() )
                    {
                        l.accent = accent;
                    }
                }
            }
        }
        // The installer's style sheet colours (stylesheet-light.qss and its
        // dark counterpart, tools/dark-stylesheet.py).
        l.window = QColor( l.dark ? "#1C1E24" : "#F3F5FA" );
        l.card = QColor( l.dark ? "#2A2C33" : "#FFFFFF" );
        l.border = QColor( l.dark ? "#4A4E59" : "#D5DAE5" );
        l.text = QColor( l.dark ? "#F3F4F8" : "#1B1D24" );
        l.subtext = QColor( l.dark ? "#A9AFBD" : "#5D6475" );
        l.free = QColor( l.dark ? "#33363F" : "#E8EBF2" );
        l.hatch = QColor( l.dark ? "#5A5F6B" : "#B4BAC8" );
        return l;
    }();
    return result;
}

QColor
mixed( const QColor& a, const QColor& b, qreal t )
{
    return QColor::fromRgbF( float( a.redF() * ( 1 - t ) + b.redF() * t ),
                             float( a.greenF() * ( 1 - t ) + b.greenF() * t ),
                             float( a.blueF() * ( 1 - t ) + b.blueF() * t ) );
}

// "40.00 GB", "1.82 TB", "512 MB" (binary units, as Windows' Disk Management
// and VeltOS Disk Management write them; the installer's language decides
// the decimal mark: Calamares sets the default locale when a language is
// chosen).
QString
sizeText( double bytes )
{
    QLocale locale;
    locale.setNumberOptions( QLocale::OmitGroupSeparator );
    constexpr double KiB = 1024.0, MiB = KiB * 1024, GiB = MiB * 1024, TiB = GiB * 1024;
    if ( bytes >= TiB )
    {
        return locale.toString( bytes / TiB, 'f', 2 ) + QStringLiteral( " TB" );
    }
    if ( bytes >= GiB )
    {
        return locale.toString( bytes / GiB, 'f', 2 ) + QStringLiteral( " GB" );
    }
    if ( bytes >= MiB )
    {
        return locale.toString( qRound64( bytes / MiB ) ) + QStringLiteral( " MB" );
    }
    return locale.toString( qRound64( qMax( 0.0, bytes ) / KiB ) ) + QStringLiteral( " KB" );
}

// Calamares' sizes in a text ("40.00 GiB", "1628MiB") in VeltOS' form.
// Translations may drop the "i" ("1628 MB" in Turkish): such sizes are
// Calamares' binary ones too and are rewritten from 1024 on, so the
// result of this function stays as it is.
QString
windowsSizes( const QString& text )
{
    static const QRegularExpression size( QStringLiteral( "(\\d+(?:[.,]\\d+)?) ?([KMGT])(i?)B\\b" ) );
    auto matches = size.globalMatch( text );
    if ( !matches.hasNext() )
    {
        return text;
    }
    QString result;
    qsizetype last = 0;
    while ( matches.hasNext() )
    {
        const QRegularExpressionMatch match = matches.next();
        QString number = match.captured( 1 );
        number.replace( QLatin1Char( ',' ), QLatin1Char( '.' ) );
        const double value = number.toDouble();
        const int power = int( QStringLiteral( "KMGT" ).indexOf( match.captured( 2 ) ) ) + 1;
        result += text.mid( last, match.capturedStart() - last );
        if ( match.captured( 3 ).isEmpty() && value < 1024 )
        {
            result += match.captured( 0 );
        }
        else
        {
            result += sizeText( value * std::pow( 1024.0, power ) );
        }
        last = match.capturedEnd();
    }
    return result + text.mid( last );
}

bool
isFree( const QModelIndex& index )
{
    return !index.isValid() || index.data( IsFreeSpaceRole ).toBool();
}

// New partitions in the accent colour (VeltOS itself fully, its helpers
// lighter); partitions already on the disk in calm colours chosen by their
// number, so a partition keeps its colour in every picture of the page.
QColor
partitionColour( const QModelIndex& index )
{
    const Look& l = look();
    if ( isFree( index ) )
    {
        return l.free;
    }
    if ( index.data( IsPartitionNewRole ).toBool() )
    {
        const QString mount = index.siblingAtColumn( MountPointColumn ).data().toString();
        if ( mount == QLatin1String( "/" ) )
        {
            return l.accent;
        }
        if ( index.data( FileSystemTypeRole ).toInt() == FsLinuxSwap )
        {
            return mixed( l.accent, l.card, 0.6 );
        }
        if ( mount.contains( QLatin1String( "/efi" ) ) )
        {
            return mixed( l.accent, l.card, 0.45 );
        }
        return mixed( l.accent, l.card, 0.25 );
    }
    static const QColor existing[] = {
        QColor( "#8764B8" ), QColor( "#5D6B82" ), QColor( "#0E7C86" ),
        QColor( "#C19C00" ), QColor( "#498205" ), QColor( "#CA5010" ),
    };
    static const QRegularExpression number( QStringLiteral( "(\\d+)$" ) );
    const int n = number.match( index.data( PartitionPathRole ).toString() ).captured( 1 ).toInt();
    return existing[ ( qMax( n, 1 ) - 1 ) % int( std::size( existing ) ) ];
}

// The name in the legend: the system found on the partition, its label, or
// its device name; Calamares' own words for new partitions.
QString
partitionName( const QModelIndex& index )
{
    const auto tr = []( const char* text, const char* comment = nullptr )
    { return QCoreApplication::translate( "PartitionLabelsView", text, comment ); };
    if ( index.data( IsPartitionNewRole ).toBool() )
    {
        const QString label = index.data( FileSystemLabelRole ).toString();
        const QString mount = index.siblingAtColumn( MountPointColumn ).data().toString();
        if ( label.compare( QLatin1String( "veltos" ), Qt::CaseInsensitive ) == 0 || ( label.isEmpty() && mount == "/" ) )
        {
            return QStringLiteral( "VeltOS" );
        }
        if ( !label.isEmpty() )
        {
            return label.left( 1 ).toUpper() + label.mid( 1 );
        }
        if ( mount.contains( QLatin1String( "/efi" ) ) )
        {
            return tr( "EFI system", "@label" );
        }
        if ( index.data( FileSystemTypeRole ).toInt() == FsLinuxSwap )
        {
            return tr( "Swap", "@label" );
        }
        return mount.isEmpty() ? tr( "New partition", "@label" ) : mount;
    }
    const QString system = index.data( OsproberNameRole ).toString();
    if ( !system.isEmpty() )
    {
        return system;
    }
    const QString label = index.data( FileSystemLabelRole ).toString();
    if ( !label.isEmpty() && !isFree( index ) )
    {
        return label;
    }
    QString name = index.data().toString();
    if ( name.startsWith( QLatin1String( "/dev/" ) ) )
    {
        name.remove( 0, 5 );
    }
    return name;
}

// "23.69 GB  NTFS"; free space and partitions without a known file system
// show only their size.
QString
partitionInfo( const QModelIndex& index )
{
    const QString size = sizeText( double( index.data( SizeRole ).toLongLong() ) );
    const int type = index.data( FileSystemTypeRole ).toInt();
    if ( isFree( index ) || type == FsUnknown || type == FsExtended || type == FsUnformatted )
    {
        return size;
    }
    return size + QStringLiteral( "  " ) + index.siblingAtColumn( FileSystemColumn ).data().toString();
}

void
collect( const QAbstractItemModel* model, const QModelIndex& parent, QModelIndexList& out )
{
    for ( int row = 0; row < model->rowCount( parent ); ++row )
    {
        const QModelIndex index = model->index( row, 0, parent );
        out.append( index );
        if ( model->hasChildren( index ) )
        {
            collect( model, index, out );
        }
    }
}

// Diagonal lines over unallocated space, as Windows' Disk Management shows it.
void
hatch( QPainter& p, const QRectF& area )
{
    p.save();
    p.setClipRect( area, Qt::IntersectClip );
    QColor line = look().hatch;
    line.setAlphaF( 0.7f );
    p.setPen( QPen( line, 1 ) );
    for ( qreal x = area.left() - area.height(); x < area.right(); x += 7 )
    {
        p.drawLine( QPointF( x, area.bottom() ), QPointF( x + area.height(), area.top() ) );
    }
    p.restore();
}

// One rounded bar with the partitions as coloured parts.
struct Bar
{
    QPainter& p;
    QRectF rect;
    QPainterPath shape;

    Bar( QPainter& painter, const QRectF& area )
        : p( painter )
        , rect( area )
    {
        shape.addRoundedRect( rect, 6, 6 );
        p.save();
        p.setClipPath( shape );
        p.fillRect( rect, look().card );
    }

    void part( QRectF area, const QColor& colour, bool free, bool hovered, bool last )
    {
        area.setTop( rect.top() );
        area.setBottom( rect.bottom() );
        if ( !last )
        {
            area.setRight( area.right() - 2 );  // a thin gap between partitions
        }
        p.fillRect( area, colour );
        if ( free )
        {
            hatch( p, area );
        }
        if ( hovered )
        {
            p.fillRect( area, QColor( 255, 255, 255, look().dark ? 40 : 70 ) );
        }
    }

    // The chosen partition: a ring in the text colour with a gap in the
    // background colour, as Windows 11 marks focus.
    void ring( const QRectF& area )
    {
        const Look& l = look();
        p.setBrush( Qt::NoBrush );
        p.setPen( QPen( l.text, 2 ) );
        p.drawRoundedRect( area.adjusted( 1, 1, -3, -1 ), 5, 5 );
        p.setPen( QPen( l.card, 1 ) );
        p.drawRoundedRect( area.adjusted( 2.5, 2.5, -4.5, -2.5 ), 3, 3 );
    }

    ~Bar()
    {
        p.restore();
        p.setBrush( Qt::NoBrush );
        p.setPen( QPen( look().border, 1 ) );
        p.drawPath( shape );
    }
};

// A row of the legend: a colour square, the name and the size underneath.
void
drawLegendEntry( QPainter& p,
                 const QRect& r,
                 const QColor& colour,
                 bool free,
                 const QString& name,
                 const QString& info,
                 const QFont& font )
{
    const Look& l = look();
    const QFontMetrics metrics( font );
    const int line = metrics.height();
    const int textLeft = qMax( line - 2, 18 );  // Calamares' LABEL_PARTITION_SQUARE_MARGIN
    const QRectF square( r.x() + 1.5, r.y() + ( line - 12 ) / 2.0 + 0.5, 11, 11 );
    p.setPen( free ? QPen( l.hatch, 1 ) : QPen( Qt::NoPen ) );
    p.setBrush( colour );
    p.drawRoundedRect( square, 3, 3 );

    const int x = r.x() + textLeft;
    const int width = qMax( 0, r.right() - x + 1 );
    QFont bold = font;
    bold.setWeight( QFont::DemiBold );
    p.setFont( bold );
    p.setPen( l.text );
    p.drawText( QRect( x, r.y(), width, line ),
                Qt::AlignLeft | Qt::AlignVCenter,
                QFontMetrics( bold ).elidedText( name, Qt::ElideRight, width ) );
    p.setFont( font );
    p.setPen( l.subtext );
    p.drawText( QRect( x, r.y() + line, width, line ),
                Qt::AlignLeft | Qt::AlignVCenter,
                metrics.elidedText( info, Qt::ElideRight, width ) );
}

// The disk list's text with VeltOS' sizes ("vda - 40.00 GB (/dev/vda)").
class SizeTextModel : public QIdentityProxyModel
{
public:
    using QIdentityProxyModel::QIdentityProxyModel;

    QVariant data( const QModelIndex& index, int role ) const override
    {
        const QVariant value = QIdentityProxyModel::data( index, role );
        if ( role == Qt::DisplayRole && value.typeId() == QMetaType::QString )
        {
            return windowsSizes( value.toString() );
        }
        return value;
    }
};

// Drop-down lists drawn by a styled delegate, so that the style sheet's
// "QComboBox QAbstractItemView::item" rules reach the rows (Qt's own combo
// box delegate ignores them).
class ListDelegate : public QStyledItemDelegate
{
public:
    using QStyledItemDelegate::QStyledItemDelegate;

protected:
    void initStyleOption( QStyleOptionViewItem* option, const QModelIndex& index ) const override
    {
        QStyledItemDelegate::initStyleOption( option, index );
        option->text = windowsSizes( option->text );
        // Icons as small as in the box (the list's own size drew the disk
        // icon at 32 px and cut the disk's name short).
        if ( const auto* combo = qobject_cast< const QComboBox* >( parent() ) )
        {
            option->decorationSize = combo->iconSize();
        }
    }
};

}  // namespace

// Paints Calamares' disk pictures; one instance for the application.
class DiskPictures : public QObject
{
    Q_OBJECT

public:
    static DiskPictures* instance()
    {
        static DiskPictures* pictures = new DiskPictures( QCoreApplication::instance() );
        return pictures;
    }

    void watch( QWidget* widget )
    {
        const QByteArray kind = widget->metaObject()->className();
        if ( kind == "PartitionBarsView" || kind == "PartitionLabelsView" )
        {
            if ( auto* view = qobject_cast< QAbstractItemView* >( widget ) )
            {
                view->viewport()->installEventFilter( this );
                connect( view->viewport(), &QObject::destroyed, this, &DiskPictures::gone, Qt::UniqueConnection );
            }
        }
        else if ( kind == "PartitionSplitterWidget" )
        {
            widget->installEventFilter( this );
            connect( widget, &QObject::destroyed, this, &DiskPictures::gone, Qt::UniqueConnection );
            connect( widget,
                     SIGNAL( partitionResized( QString, qint64, qint64 ) ),
                     this,
                     SLOT( splitChanged( QString, qint64, qint64 ) ),
                     Qt::UniqueConnection );
        }
        else if ( kind == "PartResizerWidget" || kind == "PartWidget" )
        {
            widget->installEventFilter( this );
        }
        else if ( kind == "Calamares::Widgets::PrettyRadioButton" )
        {
            makeCard( widget );
        }
        else if ( auto* combo = qobject_cast< QComboBox* >( widget ) )
        {
            useListDelegate( combo );
            combo->installEventFilter( this );
            wrapDiskList( combo );
        }
        else if ( auto* spin = qobject_cast< QSpinBox* >( widget );
                  spin && spin->objectName() == QLatin1String( "sizeSpinBox" ) )
        {
            // Sizes as the rest of VeltOS writes them (Calamares' values are
            // MiB, which Windows and VeltOS call MB).
            spin->setSuffix( QStringLiteral( " MB" ) );
            spin->installEventFilter( this );
            connect( spin, &QSpinBox::valueChanged, this, &DiskPictures::sizeChanged, Qt::UniqueConnection );
        }
        else if ( qobject_cast< QLabel* >( widget ) )
        {
            widget->installEventFilter( this );
        }
    }

    // The partition page's choices ("Erase disk", "Install alongside" ...)
    // as Windows 11 setup's option cards: the style sheet draws the card
    // (Calamares' PrettyRadioButton is a plain QWidget, which draws a style
    // sheet background only with WA_StyledBackground), the chosen one with
    // an accent border (property veltosChecked), and a click anywhere on
    // the card chooses it.
    void makeCard( QWidget* card )
    {
        if ( card->property( "veltosCard" ).toBool() )
        {
            return;  // polished again after a change of veltosChecked
        }
        card->setProperty( "veltosCard", true );
        card->setAttribute( Qt::WA_StyledBackground );
        card->setAttribute( Qt::WA_Hover );
        card->setContentsMargins( 14, 10, 14, 10 );
        card->installEventFilter( this );
        if ( QWidget* list = card->parentWidget(); list && list->layout() )
        {
            list->layout()->setSpacing( 8 );
        }
        if ( auto* radio = card->findChild< QRadioButton* >() )
        {
            const auto mark = [ card, radio ]
            {
                card->setProperty( "veltosChecked", radio->isChecked() );
                card->style()->unpolish( card );
                card->style()->polish( card );
                card->update();
            };
            connect( radio, &QRadioButton::toggled, card, mark );
            mark();
        }
    }

    static void useListDelegate( QComboBox* combo )
    {
        const QByteArray delegate = combo->itemDelegate() ? combo->itemDelegate()->metaObject()->className() : "";
        if ( delegate == "QComboBoxDelegate" || delegate == "QComboMenuDelegate" )
        {
            combo->setItemDelegate( new ListDelegate( combo ) );
        }
    }

    void forget( QWidget* widget )
    {
        widget->removeEventFilter( this );
        if ( auto* view = qobject_cast< QAbstractItemView* >( widget ) )
        {
            view->viewport()->removeEventFilter( this );
        }
    }

protected:
    bool eventFilter( QObject* object, QEvent* event ) override
    {
        switch ( event->type() )
        {
        case QEvent::Paint:
            return paint( object, event );
        case QEvent::MouseMove:
        case QEvent::Leave:
            if ( auto* view = viewOf( object ) )
            {
                const QModelIndex now = event->type() == QEvent::Leave
                    ? QModelIndex()
                    : view->indexAt( static_cast< QMouseEvent* >( event )->position().toPoint() );
                if ( QModelIndex( m_hovered.value( object ) ) != now )
                {
                    m_hovered.insert( object, now );
                    static_cast< QWidget* >( object )->update();
                }
            }
            break;
        // The size box: arrows, arrow keys, Page Up/Down and the mouse wheel
        // step the value; typed digits do not (a half-typed number must not
        // resize the partition).
        case QEvent::MouseButtonPress:
        case QEvent::MouseButtonDblClick:
        case QEvent::Wheel:
            if ( qobject_cast< QSpinBox* >( object ) )
            {
                m_stepping.insert( object );
                if ( event->type() == QEvent::Wheel )
                {
                    QTimer::singleShot( 0, this, [ this, object ] { m_stepping.remove( object ); } );
                }
            }
            break;
        case QEvent::KeyPress:
            if ( qobject_cast< QSpinBox* >( object ) )
            {
                const int key = static_cast< QKeyEvent* >( event )->key();
                if ( key == Qt::Key_Up || key == Qt::Key_Down || key == Qt::Key_PageUp || key == Qt::Key_PageDown )
                {
                    m_stepping.insert( object );
                }
            }
            break;
        case QEvent::MouseButtonRelease:
            if ( object->property( "veltosCard" ).toBool()
                 && static_cast< QMouseEvent* >( event )->button() == Qt::LeftButton )
            {
                // A click on the card's padding (the radio button and its
                // text take their own clicks).
                if ( auto* radio = object->findChild< QRadioButton* >(); radio && !radio->isChecked() )
                {
                    radio->click();
                }
            }
            m_stepping.remove( object );
            break;
        case QEvent::KeyRelease:
        case QEvent::FocusOut:
            m_stepping.remove( object );
            break;
        default:
            break;
        }
        return false;
    }

private Q_SLOTS:
    void gone( QObject* object )
    {
        m_hovered.remove( object );
        m_splits.remove( object );
        m_stepping.remove( object );
    }

    // A step of the size box finishes the edit at once: Calamares then fits
    // the partition into the free space and writes the size it really got
    // back into the box (a value past the end becomes the largest one).
    void sizeChanged( int )
    {
        auto* spin = qobject_cast< QSpinBox* >( sender() );
        if ( !spin )
        {
            return;
        }
        if ( m_stepping.contains( spin ) )
        {
            QMetaObject::invokeMethod( spin, "editingFinished" );
        }
        const auto parts = spin->window()->findChildren< QWidget* >();
        for ( QWidget* part : parts )
        {
            if ( qstrcmp( part->metaObject()->className(), "PartWidget" ) == 0 )
            {
                part->update();
            }
        }
    }

    void splitChanged( const QString& path, qint64 size, qint64 next )
    {
        m_splits.insert( sender(), { path, size, next } );
        if ( auto* widget = qobject_cast< QWidget* >( sender() ) )
        {
            widget->update();
        }
    }

private:
    struct Split
    {
        QString path;
        qint64 size = -1;
        qint64 next = -1;
    };

    using QObject::QObject;

    // The bars or legend view whose viewport this is.
    static QAbstractItemView* viewOf( QObject* object )
    {
        auto* widget = qobject_cast< QWidget* >( object );
        auto* view = widget ? qobject_cast< QAbstractItemView* >( widget->parentWidget() ) : nullptr;
        if ( !view || view->viewport() != widget )
        {
            return nullptr;
        }
        const QByteArray kind = view->metaObject()->className();
        return kind == "PartitionBarsView" || kind == "PartitionLabelsView" ? view : nullptr;
    }

    // The disk list (Calamares' DeviceModel) through SizeTextModel. Rows stay
    // the same, so Calamares' "currentIndex() is the disk's row" holds; the
    // swap happens without signals so no disk change is reported.
    static void wrapDiskList( QComboBox* combo )
    {
        QAbstractItemModel* model = combo->model();
        if ( !model || qstrcmp( model->metaObject()->className(), "DeviceModel" ) != 0 )
        {
            return;
        }
        auto* sizes = combo->findChild< QIdentityProxyModel* >( QStringLiteral( "veltos-sizes" ),
                                                                Qt::FindDirectChildrenOnly );
        if ( !sizes )
        {
            sizes = new SizeTextModel( combo );
            sizes->setObjectName( QStringLiteral( "veltos-sizes" ) );
        }
        const QSignalBlocker blocker( combo );
        const int current = combo->currentIndex();
        sizes->setSourceModel( model );
        combo->setModel( sizes );
        combo->setCurrentIndex( current );
    }

    bool paint( QObject* object, QEvent* event )
    {
        if ( auto* view = viewOf( object ) )
        {
            const QModelIndex hovered = view->selectionMode() == QAbstractItemView::NoSelection
                ? QModelIndex()
                : QModelIndex( m_hovered.value( object ) );
            if ( qstrcmp( view->metaObject()->className(), "PartitionBarsView" ) == 0 )
            {
                paintBars( view, hovered );
            }
            else
            {
                paintLegend( view, hovered );
            }
            return true;
        }
        auto* widget = qobject_cast< QWidget* >( object );
        if ( widget && qstrcmp( widget->metaObject()->className(), "PartResizerWidget" ) == 0 )
        {
            paintResizer( widget );
            return true;
        }
        if ( widget && qstrcmp( widget->metaObject()->className(), "PartWidget" ) == 0 )
        {
            paintPart( widget );
            return true;
        }
        if ( auto* handle = qobject_cast< QLabel* >( object ); handle && handle->parentWidget()
             && qstrcmp( handle->parentWidget()->metaObject()->className(), "PartResizerWidget" ) == 0 )
        {
            paintHandle( handle );
            return true;
        }
        if ( widget && qstrcmp( widget->metaObject()->className(), "PartitionSplitterWidget" ) == 0 )
        {
            // Calamares works out where its resize handle is while it paints
            // (m_resizeHandleX), and dragging needs that: it paints first,
            // then this picture covers it.
            static_cast< QObject* >( widget )->event( event );
            paintSplitter( widget );
            return true;
        }
        if ( auto* combo = qobject_cast< QComboBox* >( object ) )
        {
            wrapDiskList( combo );
        }
        else if ( auto* label = qobject_cast< QLabel* >( object ) )
        {
            const QString text = windowsSizes( label->text() );
            if ( text != label->text() )
            {
                label->setText( text );
            }
        }
        return false;
    }

    static bool isSelected( const QAbstractItemView* view, const QModelIndex& index )
    {
        return view->selectionMode() != QAbstractItemView::NoSelection && view->selectionModel()
            && view->selectionModel()->isSelected( index );
    }

    static void paintBars( QAbstractItemView* view, const QModelIndex& hovered )
    {
        QWidget* viewport = view->viewport();
        QPainter p( viewport );
        p.fillRect( viewport->rect(), look().window );
        p.setRenderHint( QPainter::Antialiasing );
        const int height = qMin( view->height(), view->sizeHint().height() );
        QModelIndexList indexes;
        if ( view->model() )
        {
            collect( view->model(), QModelIndex(), indexes );
        }
        QRectF chosen;
        {
            Bar bar( p, QRectF( 0.5, 0.5, view->width() - 1.0, height - 1.0 ) );
            bool any = false;
            for ( const QModelIndex& index : std::as_const( indexes ) )
            {
                const QRect r = view->visualRect( index );
                if ( r.isNull() )
                {
                    continue;
                }
                any = true;
                const bool last = r.right() >= view->width() - 2;
                bar.part( r, partitionColour( index ), isFree( index ), index == hovered, last );
                if ( isSelected( view, index ) )
                {
                    chosen = QRectF( r.x(), bar.rect.top(), r.width(), bar.rect.height() );
                }
            }
            if ( !any )
            {
                bar.part( bar.rect, look().free, true, false, true );  // no partition table
            }
            if ( !chosen.isNull() )
            {
                bar.ring( chosen );
            }
        }
    }

    static void paintLegend( QAbstractItemView* view, const QModelIndex& hovered )
    {
        const Look& l = look();
        QWidget* viewport = view->viewport();
        QPainter p( viewport );
        p.fillRect( viewport->rect(), l.window );
        p.setRenderHint( QPainter::Antialiasing );
        const QFont font = view->font();
        const int line = QFontMetrics( font ).height();
        QAbstractItemModel* model = view->model();
        if ( !model )
        {
            return;
        }
        QModelIndexList indexes;
        collect( model, QModelIndex(), indexes );
        for ( const QModelIndex& index : std::as_const( indexes ) )
        {
            QRect r = view->visualRect( index );
            if ( r.isNull() )
            {
                continue;
            }
            r.translate( 0, LabelsTop );
            const bool selected = isSelected( view, index );
            if ( selected || index == hovered )
            {
                const QRectF box = QRectF( r ).adjusted( -6.5, -3.5, 6.5, 2.5 );
                p.setPen( selected ? QPen( l.accent, 1 ) : QPen( Qt::NoPen ) );
                p.setBrush( selected ? mixed( l.window, l.accent, 0.12 ) : mixed( l.window, l.text, 0.06 ) );
                p.drawRoundedRect( box, 5, 5 );
            }
            drawLegendEntry( p, r, partitionColour( index ), isFree( index ), partitionName( index ),
                             partitionInfo( index ), font );
        }
        if ( model->rowCount() == 0 )
        {
            // No partition table (or one Calamares cannot read): the whole
            // disk, with the size from the disk list.
            drawLegendEntry( p,
                             QRect( 0, LabelsTop, view->width(), 2 * line ),
                             l.free,
                             true,
                             QCoreApplication::translate(
                                 "PartitionLabelsView", "Unpartitioned space or unknown partition table", "@info" ),
                             diskSize( view ),
                             font );
        }
    }

    // The size in the disk list of the page the view is on.
    static QString diskSize( QWidget* view )
    {
        static const QRegularExpression size( QStringLiteral( "\\d+(?:[.,]\\d+)? (?:KB|MB|GB|TB)" ) );
        for ( QWidget* page = view->parentWidget(); page; page = page->parentWidget() )
        {
            const auto combos = page->findChildren< QComboBox* >();
            for ( QComboBox* combo : combos )
            {
                const QRegularExpressionMatch match = size.match( windowsSizes( combo->currentText() ) );
                if ( match.hasMatch() )
                {
                    return match.captured( 0 );
                }
            }
        }
        return QString();
    }

    // Calamares' bars of the disk before the change, next to the splitter.
    static QAbstractItemView* beforeBars( QWidget* splitter )
    {
        const auto views = splitter->window()->findChildren< QAbstractItemView* >();
        for ( QAbstractItemView* view : views )
        {
            if ( qstrcmp( view->metaObject()->className(), "PartitionBarsView" ) == 0 && view->parentWidget()
                 && view->parentWidget()->objectName() == QLatin1String( "m_previewBeforeFrame" ) )
            {
                return view;
            }
        }
        return nullptr;
    }

    // "Install alongside": the disk after the change, with VeltOS' new
    // partition after the one that shrinks and a handle between them. The
    // parts follow PartitionSplitterWidget's arithmetic (partitions in disk
    // order without extended partitions, at least 1 % of the bar each), so
    // the handle is where Calamares expects the mouse.
    void paintSplitter( QWidget* splitter ) const
    {
        const Look& l = look();
        struct Part
        {
            qreal size;
            QColor colour;
            bool free;
        };
        QVector< Part > parts;
        int shrinking = -1;
        const Split split = m_splits.value( splitter );
        if ( QAbstractItemView* before = beforeBars( splitter ); before && before->model() )
        {
            QModelIndexList indexes;
            collect( before->model(), QModelIndex(), indexes );
            for ( const QModelIndex& index : std::as_const( indexes ) )
            {
                if ( index.data( FileSystemTypeRole ).toInt() == FsExtended )
                {
                    continue;
                }
                const QColor colour = partitionColour( index );
                if ( split.size >= 0 && index.data( PartitionPathRole ).toString() == split.path )
                {
                    shrinking = int( parts.size() );
                    parts.append( { qreal( split.size ), colour, false } );
                    parts.append( { qreal( split.next ), l.accent, false } );
                }
                else
                {
                    parts.append( { qreal( index.data( SizeRole ).toLongLong() ), colour, isFree( index ) } );
                }
            }
        }
        qreal total = 0;
        for ( const Part& part : std::as_const( parts ) )
        {
            total += part.size;
        }
        qreal adjusted = total;
        for ( Part& part : parts )
        {
            if ( part.size < 0.01 * total )
            {
                adjusted += qint64( 0.01 * total ) - part.size;
                part.size = qint64( 0.01 * total );
            }
        }

        QPainter p( splitter );
        p.fillRect( splitter->rect(), l.window );
        p.setRenderHint( QPainter::Antialiasing );
        const QRect rect = splitter->rect();
        int handle = -1;
        {
            Bar bar( p, QRectF( rect ).adjusted( 0.5, 0.5, -0.5, -0.5 ) );
            int x = rect.x();
            for ( int row = 0; row < parts.size(); ++row )
            {
                const qreal width
                    = row < parts.size() - 1 ? rect.width() * ( parts[ row ].size / adjusted ) : rect.right() - x + 1;
                if ( row == shrinking + 1 && shrinking >= 0 )
                {
                    handle = x;
                }
                bar.part( QRectF( x, rect.y(), int( width ), rect.height() ),
                          parts[ row ].colour,
                          parts[ row ].free,
                          false,
                          row == parts.size() - 1 );
                x += width;
            }
            if ( parts.isEmpty() )
            {
                bar.part( bar.rect, l.free, true, false, true );
            }
        }
        if ( handle >= 0 )
        {
            // Windows 11's slider thumb, upright: a light pill with a ring.
            const QRectF thumb( handle - 4.5, rect.top() + 0.5, 9, rect.height() - 1.0 );
            p.setPen( QPen( l.border, 1 ) );
            p.setBrush( l.dark ? QColor( "#454A55" ) : QColor( "#FFFFFF" ) );
            p.drawRoundedRect( thumb, 4.5, 4.5 );
            p.setPen( QPen( l.accent, 2, Qt::SolidLine, Qt::RoundCap ) );
            const qreal middle = thumb.center().y();
            p.drawLine( QPointF( handle, middle - 5 ), QPointF( handle, middle + 5 ) );
        }
    }

    // KPMcore's size bar in the partition dialogs: the space the partition
    // may take, hatched like unallocated space, between the two handles
    // (QLabel children as wide as the handle).
    static void paintResizer( QWidget* resizer )
    {
        int handle = 0;
        const auto labels = resizer->findChildren< QLabel* >( Qt::FindDirectChildrenOnly );
        for ( const QLabel* label : labels )
        {
            handle = qMax( handle, label->width() );
        }
        QPainter p( resizer );
        p.setRenderHint( QPainter::Antialiasing );
        const QRectF area( handle + 0.5, 0.5, resizer->width() - 2.0 * handle - 1.0, resizer->height() - 1.0 );
        if ( area.width() < 4 )
        {
            return;
        }
        Bar bar( p, area );
        bar.part( area, look().free, true, false, true );
    }

    // The partition itself: the accent colour for a new one, a calm colour
    // for one being edited, with its name and size (the size box's value,
    // which Calamares keeps equal to the partition's size).
    static void paintPart( QWidget* part )
    {
        const Look& l = look();
        QWidget* dialog = part->window();
        const bool creating = qstrcmp( dialog->metaObject()->className(), "CreatePartitionDialog" ) == 0;
        const QRectF r = QRectF( part->rect() ).adjusted( 0.5, 0.5, -0.5, -0.5 );
        if ( r.width() < 4 )
        {
            return;
        }
        QPainter p( part );
        p.setRenderHint( QPainter::Antialiasing );
        p.setPen( Qt::NoPen );
        p.setBrush( creating ? l.accent : QColor( "#5D6B82" ) );
        p.drawRoundedRect( r, 6, 6 );

        QString size;
        if ( const auto* spin = dialog->findChild< QSpinBox* >( QStringLiteral( "sizeSpinBox" ) ) )
        {
            size = sizeText( double( spin->value() ) * 1024 * 1024 );
        }
        const QString name = creating
            ? QCoreApplication::translate( "PartitionLabelsView", "New partition", "@label" )
            : QString();
        QFont font = part->font();
        const QFontMetrics metrics( font );
        const int width = int( r.width() ) - 12;
        if ( width < metrics.horizontalAdvance( size ) )
        {
            return;  // too narrow for text, as Windows' Disk Management
        }
        p.setPen( Qt::white );
        const int line = metrics.height();
        const int top = int( r.center().y() ) - ( name.isEmpty() ? line / 2 : line );
        if ( !name.isEmpty() )
        {
            QFont bold = font;
            bold.setWeight( QFont::DemiBold );
            p.setFont( bold );
            p.drawText( QRect( int( r.x() ) + 6, top, width, line ),
                        Qt::AlignCenter,
                        QFontMetrics( bold ).elidedText( name, Qt::ElideRight, width ) );
        }
        p.setFont( font );
        p.drawText( QRect( int( r.x() ) + 6, top + ( name.isEmpty() ? 0 : line ), width, line ), Qt::AlignCenter, size );
    }

    // A handle: Windows 11's slider thumb, upright.
    static void paintHandle( QLabel* handle )
    {
        const Look& l = look();
        QPainter p( handle );
        p.setRenderHint( QPainter::Antialiasing );
        const QRectF thumb = QRectF( handle->rect() ).adjusted( 0.5, 0.5, -0.5, -0.5 );
        p.setPen( QPen( l.border, 1 ) );
        p.setBrush( l.dark ? QColor( "#454A55" ) : QColor( "#FFFFFF" ) );
        p.drawRoundedRect( thumb, thumb.width() / 2, thumb.width() / 2 );
        p.setPen( QPen( l.accent, 2, Qt::SolidLine, Qt::RoundCap ) );
        const qreal x = thumb.center().x();
        const qreal middle = thumb.center().y();
        p.drawLine( QPointF( x, middle - 7 ), QPointF( x, middle + 7 ) );
    }

    QHash< QObject*, QPersistentModelIndex > m_hovered;
    QHash< QObject*, Split > m_splits;
    QSet< QObject* > m_stepping;  // size boxes being stepped right now
};

class InstallerStyle : public QProxyStyle
{
public:
    InstallerStyle()
        : QProxyStyle( QStyleFactory::create( QStringLiteral( "kvantum" ) ) )
    {
    }

    // Drop-down lists stay plain lists under their box, drawn by the style
    // sheet. Kvantum turns them into translucent menus with a shadow and
    // moves them up and left by the shadow's size, so they covered their
    // own box (product owner, 2026-10-23: "the area that opens overlaps");
    // it also gives the list a transparent style sheet when it finds Qt's
    // menu delegate, hence the delegate first.
    static bool kvantumKeepsOff( const QWidget* widget )
    {
        const QByteArray kind = widget->metaObject()->className();
        return kind == "QComboBoxPrivateContainer" || kind == "QComboBoxListView";
    }

    void polish( QWidget* widget ) override
    {
        if ( auto* combo = qobject_cast< QComboBox* >( widget ) )
        {
            DiskPictures::useListDelegate( combo );
        }
        if ( !kvantumKeepsOff( widget ) )
        {
            QProxyStyle::polish( widget );
        }
        DiskPictures::instance()->watch( widget );
    }

    void unpolish( QWidget* widget ) override
    {
        DiskPictures::instance()->forget( widget );
        if ( !kvantumKeepsOff( widget ) )
        {
            QProxyStyle::unpolish( widget );
        }
    }

    // KPMcore sizes the handles of its size bar from the splitter width,
    // asked without a widget (PartResizerWidget::handleWidth); real
    // splitters ask with theirs and keep Kvantum's width. 11 px leaves room
    // for a slider thumb that can be grabbed.
    int pixelMetric( PixelMetric metric, const QStyleOption* option, const QWidget* widget ) const override
    {
        if ( metric == PM_SplitterWidth && !widget && !option )
        {
            return 11;
        }
        return QProxyStyle::pixelMetric( metric, option, widget );
    }

    // The list exactly under the box and as wide as it (Kvantum's rect
    // leaves room for its menu shadow, 15 px up and left of the box).
    QRect subControlRect( ComplexControl control,
                          const QStyleOptionComplex* option,
                          SubControl sub,
                          const QWidget* widget ) const override
    {
        if ( control == CC_ComboBox && sub == SC_ComboBoxListBoxPopup )
        {
            return option->rect;
        }
        return QProxyStyle::subControlRect( control, option, sub, widget );
    }

    using QProxyStyle::polish;
    using QProxyStyle::unpolish;
};

class InstallerStylePlugin : public QStylePlugin
{
    Q_OBJECT
    Q_PLUGIN_METADATA( IID QStyleFactoryInterface_iid FILE "veltos-installer.json" )

public:
    QStyle* create( const QString& key ) override
    {
        return key.compare( QLatin1String( "veltos-installer" ), Qt::CaseInsensitive ) == 0 ? new InstallerStyle
                                                                                            : nullptr;
    }
};

#include "installerstyle.moc"
