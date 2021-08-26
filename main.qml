import QtQuick 2.15
import QtQuick.Controls 2.15

import QtMultimedia 5.15
import AugRealityLib 1.0 // Our custom "library".

Item {
    id: item1 // Our root item.
    width: 800
    height: 480
    visible: true

    Camera {
        id: camera

        viewfinder.resolution: "640x480" // We want video frames to be this size

        focus {
            // This is important on Android for ensuring things are in focus.
            focusMode: Camera.FocusContinuous
        }

    }

    // This is the "screen" where our video is displayed.
    VideoOutput {
        id: videoOutput
        objectName: "videoOutput"
        x: 80 
        y: 0
        width: 640
        height: 480

        // Centre in parent and vertically fill it.
        anchors.verticalCenter: parent.verticalCenter
        source: camera
        anchors.fill: parent
        fillMode: VideoOutput.PreserveAspectFit

        // For Android, when the phone gets turned around.
        autoOrientation: true

        focus : visible
        filters: [ augRealityFilter ] // Reference our custom filter.

        // The below is one way to tell the user that tracking is lost.
        // It's not the prettiest, so feel free to change it.
        Rectangle {
            id: trackingTextBackground
            visible: !augRealityFilter.trackingStatus
            width: 250
            height: 75
            color: "#ffffff"
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: 20

            Text {
                id: trackingLostText
                color: "#aa0000"
                text: qsTr("Tracking Lost!")
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                font.pixelSize: 32
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.family: "Arial"
                minimumPixelSize: 12
                font.weight: Font.Bold
            }
        }
    }

    // Creating this item allows other QML objects to refer to our filter via
    // its ID.
    AugRealityFilter {
        id: augRealityFilter

        videoOutputOrientation: videoOutput.orientation
    }

    // Text for displaying framerate and/or debugging info.
    Text {
        id: fpsText
        //z: 0
        color: "#55ff55"
        visible: false
        width: item1.width/2
        height: item1.height/3
        text: augRealityFilter.framerateText
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        font.pixelSize: 32
        anchors.bottomMargin: 8
        anchors.rightMargin: 8
    }


}
