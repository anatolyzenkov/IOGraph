package com.iographica.core;

import java.awt.Color;
import java.awt.GraphicsDevice;
import java.awt.GraphicsEnvironment;
import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.Properties;
import java.util.jar.Attributes;
import java.util.jar.JarFile;
import java.util.jar.JarInputStream;
import java.util.jar.Manifest;
import java.util.prefs.Preferences;

import javax.swing.JFrame;

import com.iographica.utils.debug.gui.DebugConsole;

public class Data {
	public static final String APPLICATION_NAME = "IOGraph";
	public static final String APPLICATION_VERSION = "1.0.1";
	public static final String WEBSITE_URL = "http://iographica.com/";
	public static final String UPDATE_URL = "http://iographica.com/update/";
	public static final String FACEBOOK_PAGE_URL = "http://www.facebook.com/pages/IOGraphica/317794951637";
	public static final String FAQ_URL = "http://iographica.com/faq/";
	public static final String RESOURCE_DIRECTORY = "/recources/";
	public static final String IOGRAPH_NODE_NAME = "/com/iographica/iograph";
	public static final String ZENKOV_WEBSITE_URL = "http://anatolyzenkov.com/";
	public static final String SHIPILOV_WEBSITE_URL = "http://andreyshipilov.com/";
	public static final String DONATE_URL = "http://iographica.com/donate/";
	public static final int MAIN_FRAME_WIDTH = 465;
	public static final int PANEL_HEIGHT = 66;
	public static final Color TEXT_COLOR = new Color(0x313131);
	public static final Color BACKGROUND_COLOR = new Color(0xCCCCCC);
	public static final Color OUT_OF_FOCUS_BACKGROUND_COLOR = new Color(0xDDDDDD);

	public static final String USE_MULTIPLE_MONITORS = "useMultipleMonitors";
	public static final String IGNORE_MOUSE_STOPS = "ignoreMouseStops";
	public static final String AUTOMATIC_UPDATE = "automaticUpdate";
	public static final String USE_COLOR_SCHEME = "useColorScheme";
	public static final String SHOW_DONATION_MESSAGE = "showDonationMessage";

	public static final int STOP_DRAW = 0;
	public static final int START_DRAW = 1;
	public static final int UPDATE_BACKGROUND = 2;
	public static final int MULTI_MONITOR_USAGE_CHANGED = 3;
	public static final int BACKGROUND_USAGE_CHANGED = 4;
	public static final int OPEN_CONTROLS = 5;
	public static final int CLOSE_CONTROLS = 6;
	public static final int SAVE_IMAGE = 7;
	public static final int IMAGE_SAVED = 8;
	public static final int GET_URL = 9;
	public static final int RESET = 10;
	public static final int TIME_CHANGED = 11;
	public static final int PERIOD_CHANGED = 12;
	public static final int COLOR_SCHEME_CHANGED = 13;
	public static final int MENU_ABOUT = 14;
	public static final int SYSTEM_QUIT_REQUESTED = 15;
	public static final int SHOW_ABOUT = 16;
	public static final int CHECK_FOR_UPDATES = 17;
	public static final int CHECK_FOR_UPDATES_COMPLETE = 18;
	public static final int AUTO_CHECK_FOR_UPDATES_CHANGED = 19;
	public static final int RESET_ENABLED = 20;
	public static final int RESET_DISABLED = 21;
	public static final int IGNORE_MOUSE_STOPS_CHANGED = 22;
	public static final int MULTI_MONITOR_USAGE_CHANGING_REQUEST = 23;
	public static final int COLORFUL_SCHEME_USAGE_CHANGING_REQUEST = 24;
	public static final int BACKGROUND_USAGE_CHANGE_REQUEST = 25;
	public static final int BACKGROUND_IS_UP_TO_DATE = 26;
	public static final int CLOSE_NOTIFICATION_BAR = 27;
	public static final int OPEN_NOTIFICATION_BAR = 28;

	public static final float STROKE_WEIGHT = .45f;
	public static final int FPS = 30;
	public static final String BACKGROUND_FILE_NAME = ".iographsnapshot.png";
	public static final String BACKGROUND_PREVIEW_FILE_NAME = ".iographsnapshotsmall.png";
	public static Boolean preventControlsHiding = false;
	public static Boolean mouseTrackRecording = false;
	public static Boolean moreThanOneMonitor = false;
	public static Boolean requestedMultiMonitorUsage;
	public static Boolean requestedColorfulSchemeUsage;
	public static Boolean useScreenshot = false;
	public static Boolean useColorScheme = false;
	public static JFrame mainFrame;
	public static String time = "";
	public static Boolean usePeriod = false;
	public static String period = "";
	public static long trackingTime = 0;
	public static Boolean isOSX = false;
	public static Preferences prefs;
	public static Boolean isCheckingForUpdates = false;
	// private static String _version = "Not acquired from MANIFEST.MF.";
	private static String _version = "0.0.0";
	private static DebugConsole _console;

	public static void getPrefs() {
		_console = new DebugConsole();
		_console.setVisible(true);
		System.getProperties().list(System.out);
		//readManifest();
		GraphicsEnvironment e = GraphicsEnvironment.getLocalGraphicsEnvironment();
		GraphicsDevice[] a = e.getScreenDevices();
		moreThanOneMonitor = a.length > 1;
		prefs = Preferences.userRoot().node(IOGRAPH_NODE_NAME);
	}

	private static void readManifest() {
		// TODO: Try read version from manifest from wrapped .exe.
		Manifest manifest = null;
		Properties props = System.getProperties();
		String classpath = props.getProperty("java.class.path");
		String userdir = props.getProperty("user.dir");
		String pathtojar;
		String s = "";
		if (classpath.indexOf(File.separator) != -1) {
			if (classpath.indexOf(".jar") == classpath.length() - 4) { // Executable jar double click.
				pathtojar = "file:" + classpath;
				JarInputStream jarStream;
				try {
					jarStream = new JarInputStream(new URL(pathtojar).openStream());
					manifest = jarStream.getManifest();
				} catch (MalformedURLException e) {
					e.printStackTrace();
					s = "E1 " + classpath + " " + userdir + " " + pathtojar;
				} catch (IOException e) {
					e.printStackTrace();
					s = "E2 " + classpath + " " + userdir + " " + pathtojar;
				}
			} else { // Eclipse debug.
				pathtojar = "file:" + userdir + File.separator + "ant/MANIFEST.MF";
				try {
					manifest = new Manifest(new URL(pathtojar).openStream());
					// manifest.write(System.out);
				} catch (MalformedURLException e) {
					e.printStackTrace();
					s = "E3 " + classpath + " " + userdir + " " + pathtojar;
				} catch (IOException e) {
					e.printStackTrace();
					s = "E4 " + classpath + " " + userdir + " " + pathtojar;
				}
			}
		} else { // Jar from console.
			pathtojar = userdir + File.separator + classpath;
			try {
				JarFile jar = new JarFile(pathtojar);
				manifest = jar.getManifest();
			} catch (IOException e) {
				e.printStackTrace();
				s = "E5 " + classpath + " " + userdir + " " + pathtojar;
			}
		}
		if (manifest == null) {
			//_version = s;
			System.out.println(s);
			return;
		}
		Attributes attr = manifest.getMainAttributes();
		_version = attr.getValue("Specification-Version");
		System.out.println("Specification Version: " + _version);
	}

	public static String getApplicationVersion() {
		return _version;
	}
}