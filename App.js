import React from 'react';
import { View, Text, StyleSheet ,Button} from 'react-native';
import PaperDetectionScreen from './PaperDetectionScreen.js'; // Assuming PaperDetectionScreen.js is in the same directory

const App = () => {
  
  return (
    <View style={styles.container}>
      <PaperDetectionScreen />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default App;
