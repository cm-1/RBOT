#include <QGuiApplication>
#include <QQuickView>
#include <QQmlApplicationEngine>

#include "AugRealityFilter.h"

// This is primarily boilerplate.
int main(int argc, char *argv[])
{
    QGuiApplication app(argc, argv);
    QQuickView view;

    qmlRegisterType<AugRealityFilter>("AugRealityLib", 1, 0, "AugRealityFilter");

    // This sets our root "Item" in main.qml to match the window's size
    // if it's changed from default dimensions.
    view.setResizeMode(QQuickView::SizeRootObjectToView);

    QObject::connect(view.engine(), &QQmlEngine::quit,
                     qApp, &QGuiApplication::quit);

    view.setSource(QUrl("qrc:///main.qml"));
    view.show();

#ifdef Q_OS_ANDROID
    view.showFullScreen(); // Fullscreen on phone
#endif

    return app.exec();
}
