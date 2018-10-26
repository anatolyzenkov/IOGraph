/*
 * Based on SimpleAudioPlayer.java
 * Copyright (c) 1999 - 2001 by Matthias Pfisterer
 * All rights reserved.
 */
package com.iographica.core;

import java.io.IOException;
import java.net.URL;

import javax.sound.sampled.AudioFormat;
import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.DataLine;
import javax.sound.sampled.LineUnavailableException;
import javax.sound.sampled.SourceDataLine;

public class AudioPlayer extends Thread {
	private static final int EXTERNAL_BUFFER_SIZE = 128000;
	private String _strFilename;

	public AudioPlayer(String strFilename) {
		start();
		_strFilename = strFilename;
	}

	public void run() {
		URL sound = IOGraph.getInstance().getClass().getResource(_strFilename);
		AudioInputStream audioInputStream = null;
		try {
			audioInputStream = AudioSystem.getAudioInputStream(sound);
		} catch (Exception e) {
			e.printStackTrace();
		}
		AudioFormat audioFormat = audioInputStream.getFormat();
		if (audioFormat.getEncoding() == AudioFormat.Encoding.ULAW) {
		} else if (audioFormat.getEncoding() == AudioFormat.Encoding.ULAW) {
		}

		DataLine.Info info = new DataLine.Info(SourceDataLine.class, audioFormat);

		SourceDataLine line = null;
		try {
			line = (SourceDataLine) AudioSystem.getLine(info);
			line.open(audioFormat);
		} catch (LineUnavailableException e) {
			e.printStackTrace();
		} catch (Exception e) {
			e.printStackTrace();
		}
		line.start();
		int nBytesRead = 0;
		byte[] abData = new byte[EXTERNAL_BUFFER_SIZE];
		while (nBytesRead != -1) {
			try {
				nBytesRead = audioInputStream.read(abData, 0, abData.length);
			} catch (IOException e) {
				e.printStackTrace();
			}
			if (nBytesRead >= 0) {
				line.write(abData, 0, nBytesRead);
			}
		}
		line.drain();
		line.close();
		try {
			audioInputStream.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
}