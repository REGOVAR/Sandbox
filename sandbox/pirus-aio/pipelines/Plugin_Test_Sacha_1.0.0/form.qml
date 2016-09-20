import QtQuick 2.0
import QtWebSockets 1.0

Rectangle {
    width: 360
    height: 360

    WebSocket {
        id: socket
        url: "ws://localhost:8080/ws"
        onTextMessageReceived: {
            messageBox.text = messageBox.text + "\nReceived message: " + message
        }
        onStatusChanged: if (socket.status == WebSocket.Error) {
                             console.log("Error: " + socket.errorString)
                         } else if (socket.status == WebSocket.Open) {
                            console.debug("OPEN")
                         } else if (socket.status == WebSocket.Closed) {
                             console.debug("CLOSE")
                         }
        active: false
    }


    Text {
        id: messageBox
        text: socket.status == WebSocket.Open ? qsTr("Waiting ... ") : qsTr("Welcome!")
        anchors.centerIn: parent
    }

    MouseArea {
        anchors.fill: parent
        onClicked: {
            socket.active = !socket.active
            //Qt.quit();
        }
    }
}
