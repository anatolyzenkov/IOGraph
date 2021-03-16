package com.iographica.core;

import java.awt.AWTException;
import java.awt.GraphicsDevice;
import java.awt.GraphicsEnvironment;
import java.awt.Image;
import java.awt.Rectangle;
import java.awt.Robot;
import java.awt.event.WindowEvent;
import java.awt.event.WindowStateListener;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;

import javax.imageio.ImageIO;
import javax.swing.JFrame;

import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;

public class SnapshotManager implements IEventHandler, IEventDispatcher {
	private JFrame _mainWindow;
	private WindowStateListener _listener;
	private ArrayList<IEventHandler> _eventHandlers;
	static public final Boolean PREVIEW = true;
	static public final Boolean FULL_SIZE = false;
	static private int _pixelScale = -1;

	public SnapshotManager(JFrame mainWindow) {
		_mainWindow = mainWindow;
		_mainWindow.addWindowStateListener(new WindowStateListener() {
			public void windowStateChanged(WindowEvent e) {
				//System.out.println("State chaged ");
			}
		});
		_listener = new WindowStateListener() {
			public void windowStateChanged(WindowEvent e) {
				takeSnapshot();
			}
		};
	}

	public void onEvent(IOEvent event) {
		if (event.type != Data.UPDATE_BACKGROUND) return;
		_mainWindow.addWindowStateListener(_listener);
		_mainWindow.setState(JFrame.ICONIFIED);
	}

	private void takeSnapshot() {
		_mainWindow.removeWindowStateListener(_listener);
		Robot r;
		try {
			r = new Robot();
		} catch (AWTException e) {
			_mainWindow.setState(JFrame.NORMAL);
			e.printStackTrace();
			return;
		}
		_mainWindow.setVisible(false);

		Rectangle rect = getScreenBounds(SnapshotManager.FULL_SIZE);
		BufferedImage base = new BufferedImage(rect.width, rect.height, BufferedImage.TYPE_INT_RGB);
		base.getGraphics().fillRect(0, 0, rect.width, rect.height);
		
		BufferedImage screenshot;
		GraphicsEnvironment e = GraphicsEnvironment.getLocalGraphicsEnvironment();
		if (Data.prefs.getBoolean(Data.USE_MULTIPLE_MONITORS, true) && Data.moreThanOneMonitor) {
			GraphicsDevice[] a = e.getScreenDevices();
			for (GraphicsDevice graphicsDevice : a) {
				Rectangle sRect = graphicsDevice.getDefaultConfiguration().getBounds();
				screenshot = r.createScreenCapture(sRect);
				base.createGraphics().drawImage(screenshot, sRect.x-rect.x, sRect.y-rect.y, null);
				screenshot.flush();
				screenshot = null;
			}
		} else {
			screenshot = r.createScreenCapture(rect);
			base.createGraphics().drawImage(screenshot, 0, 0, null);
			screenshot.flush();
			screenshot = null;
		}

		Rectangle pRect = getScreenBounds(SnapshotManager.PREVIEW);
		BufferedImage pBase = new BufferedImage(pRect.width, pRect.height, BufferedImage.TYPE_INT_RGB);
		pBase.createGraphics().drawImage(base.getScaledInstance(pRect.width, pRect.height, Image.SCALE_AREA_AVERAGING), 0, 0, pRect.width, pRect.height, 0, 0, pRect.width, pRect.height, null);
		writeImage(base, Data.BACKGROUND_FILE_NAME);
		writeImage(pBase, Data.BACKGROUND_PREVIEW_FILE_NAME);

		base.flush();
		base = null;
		pBase.flush();
		pBase = null;
		new AudioPlayer(Data.RESOURCE_DIRECTORY + "Camera.wav");

		_mainWindow.setVisible(true);
		_mainWindow.setState(JFrame.NORMAL);
		dispatchEvent(Data.UPDATE_BACKGROUND);
		
		System.gc();
		dispatchEvent(Data.BACKGROUND_IS_UP_TO_DATE);
	}
	
	public static int getPixelScale() {
		if (_pixelScale == -1) {
			_pixelScale = 1;
			if (!GraphicsEnvironment.getLocalGraphicsEnvironment().getDefaultScreenDevice().getDefaultConfiguration().getDefaultTransform().isIdentity()) {
				_pixelScale = 2;
			}
		}
		return _pixelScale;
	}

	public static Rectangle getScreenBounds(Boolean preview) {
		GraphicsEnvironment e = GraphicsEnvironment.getLocalGraphicsEnvironment();
		Rectangle r = new Rectangle();
		if (Data.prefs.getBoolean(Data.USE_MULTIPLE_MONITORS, true) && Data.moreThanOneMonitor) {
			GraphicsDevice[] a = e.getScreenDevices();
			for (GraphicsDevice graphicsDevice : a) {
				r = r.union(graphicsDevice.getDefaultConfiguration().getBounds());
			}
		} else {
			r.width = e.getDefaultScreenDevice().getDisplayMode().getWidth();
			r.height = e.getDefaultScreenDevice().getDisplayMode().getHeight();
		}
		if (preview) {
			float scale = (float) Data.MAIN_FRAME_WIDTH / (float) r.width;
			r.width = Data.MAIN_FRAME_WIDTH;
			r.height = (int) (r.height * scale);
		}
		return r;
	}

	private void writeImage(BufferedImage img, String name) {
		File file = new File(name);
		file.deleteOnExit();
		try {
			ImageIO.write(img, "png", file);
		} catch (IOException err) {
			err.printStackTrace();
			return;
		}
	}

	public void addEventHandler(IEventHandler handler) {
		if (_eventHandlers == null) {
			_eventHandlers = new ArrayList<IEventHandler>();
		}
		_eventHandlers.add(handler);
	}

	private void dispatchEvent(int type) {
		if (_eventHandlers != null) {
			final IOEvent event = new IOEvent(type, this);
			for (IEventHandler handler : _eventHandlers) {
				handler.onEvent(event);
			}
		}
	}
}
