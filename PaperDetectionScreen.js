import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Image, Dimensions } from 'react-native';
import { Camera } from 'expo-camera';
import MyButton from './src/components/Button.js';
import axios from 'axios';

const { width, height } = Dimensions.get('window');  // Dimensions of the screen
const scaleX = width / 640;
const scaleY = height / 640;

const PaperDetectionScreen = () => {
    const [hasPermission, setHasPermission] = useState(null);
    const [currentFrame, setCurrentFrame] = useState(null);
    const [isRecording, setIsRecording] = useState(false);
    const cameraRef = useRef(null);
    const frameCaptureIntervalRef = useRef(null);
    const [boxes, setBoxes] = useState([]);


    useEffect(() => {
        (async () => {
            const { status } = await Camera.requestCameraPermissionsAsync();
            setHasPermission(status === 'granted');
        })();
    }, []);

    const sendImageToServer = async (base64Image) => {
        const url = 'http://192.168.100.82:5000/predict';
        console.log(height)
        console.log(width)
        axios.post(url, { image: base64Image })
            .then(response => {
                console.log('Success:', response.data);
                setBoxes(response.data.boxes);  // Assuming response data.boxes is an array of [x_min, y_min, x_max, y_max]
            })
            .catch(error => console.error('Error sending image to server:', error));
    };

    const captureFrame = async () => {
        if (cameraRef.current) {
            const photo = await cameraRef.current.takePictureAsync({
                quality: 0.5,
                base64: true,
            });
            setCurrentFrame(photo.uri); // Update the current frame
            sendImageToServer(photo.base64);
        }
    };

    const startFrameCapture = () => {
        if (!frameCaptureIntervalRef.current) {
            frameCaptureIntervalRef.current = setInterval(captureFrame, 2500); // Capture frame every 500ms
        }
    };

    const stopFrameCapture = () => {
        if (frameCaptureIntervalRef.current) {
            clearInterval(frameCaptureIntervalRef.current);
            frameCaptureIntervalRef.current = null;
        }
    };

    if (hasPermission === false) {
        return <Text>No access to camera</Text>;
    }

    const renderBoxes = () => {
        return boxes.map((box, index) => (
            <View key={index} style={{
                position: 'absolute',
                borderColor: 'red',
                borderWidth: 2,
                left: box[0] * scaleX, // x_min
                top: box[1] * scaleY, // y_min
                width: (box[2] - box[0]) * scaleX, // width
                height:(box[3] - box[1]) * scaleY, // height
            }} />
        ));
    };

    return (
        <View style={styles.container}>
            <Camera style={styles.camera} type={Camera.Constants.Type.back} ref={cameraRef}>
                {renderBoxes()}
            </Camera>
            <View style={styles.buttonContainer}>
                <MyButton onPress={() => {
                    if (isRecording) {
                        setIsRecording(false);
                        stopFrameCapture();
                    } else {
                        setIsRecording(true);
                        startFrameCapture();
                    }
                }} title={isRecording ? "Stop" : "Start"}/>
            </View>
            {currentFrame && (
                <View style={styles.previewContainer}>
                    <Image source={{ uri: currentFrame }} style={styles.preview} />
                </View>
            )}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#000',
        width: '100%',
        height:'100%'
    },
    camera: {
        flex: 1,
        borderRadius: 20,
    },
    buttonContainer: {
        position: 'absolute',
        bottom: 50,
        alignSelf: 'center',
    },
    preview: {
        width: 100,
        height: 100,
        position: 'absolute',
        bottom: 10,
        right: 10
    }
    
});

export default PaperDetectionScreen;
