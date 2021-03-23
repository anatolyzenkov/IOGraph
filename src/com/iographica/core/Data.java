package com.iographica.core;

import java.awt.Color;
import java.awt.GraphicsDevice;
import java.awt.GraphicsEnvironment;
import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.nio.file.Paths;
import java.util.Properties;
import java.util.jar.Attributes;
import java.util.jar.Manifest;
import java.util.prefs.Preferences;

import javax.swing.JFrame;

public class Data {
	public static final boolean DEBUG = false;
	public static final String APPLICATION_NAME = "IOGraph";
	public static final String WEBSITE_PROTOCOL = "https";
	public static final String WEBSITE_DOMAIN = "iographica.com";
//	public static final String WEBSITE_DOMAIN = "localhost:8888";
	public static final String WEBSITE_URL = WEBSITE_PROTOCOL + "://" + WEBSITE_DOMAIN + "/";
	public static final String UPDATE_URL = WEBSITE_URL + "update/";
	public static final String FAQ_URL = WEBSITE_URL + "faq/";
	public static final String DONATE_URL = WEBSITE_URL + "donate/";
	public static final String FACEBOOK_PAGE_URL = "https://www.facebook.com/pages/IOGraphica/317794951637";
	public static final String GIT_REPO_URL = "https://github.com/anatolyzenkov/iograph";
	public static final String RESOURCE_DIRECTORY = "/recources/";
	public static final String IOGRAPH_NODE_NAME = "/com/iographica/iograph";
	public static final String ZENKOV_WEBSITE_URL = "https://anatolyzenkov.com/";
	public static final String SHIPILOV_WEBSITE_URL = "https://andreyshipilov.com/";
	public static String _font = "none";
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
	public static final int SAVE_CSV = 29;
	public static final int CSV_SAVED = 30;
	public static final int TIME = 31;

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
	public static Boolean isTrayGUI = false;
	public static Preferences prefs;
	public static Boolean isCheckingForUpdates = false;
	// private static String _version = "Not acquired from MANIFEST.MF.";
	private static String _version = "0.0.0";

	public static void getPrefs() {
		readManifest();
		GraphicsEnvironment e = GraphicsEnvironment.getLocalGraphicsEnvironment();
		GraphicsDevice[] a = e.getScreenDevices();
		moreThanOneMonitor = a.length > 1;
		prefs = Preferences.userRoot().node(IOGRAPH_NODE_NAME);
	}

	private static void readManifest() {
		Properties props = System.getProperties();
		System.out.println("MANIFEST READING");
		System.out.println(props.getProperty("java.class.path"));
		File file = new File(props.getProperty("java.class.path"));
		String path = "";
		URL url = null;
		Manifest manifest = null;
		Attributes attr = null;
		if (file.isDirectory()) {
			System.out.println("Not jar manifest.");
			file = new File(Paths.get(file.toPath().toString(), "..", "ant", "MANIFEST.MF").toString());
			if (file.exists()) {
				path = "file:" + file.toPath().toString();
			} else {
				System.out.println("Manifest not exist.");
			}
		} else {
			System.out.println("Jar manifest. 2");
			try {
				url = IOGraph.getInstance().getClass().getResource("/META-INF/MANIFEST.MF");
				System.out.println(url.toString());
				System.out.println(url.toString());
				manifest = new Manifest(url.openStream());
				System.out.println(manifest.toString());
			} catch (MalformedURLException ue) {
				// TODO Auto-generated catch block
				System.out.println(ue.getLocalizedMessage());
				ue.printStackTrace();
			} catch (IOException ioe) {
				// TODO Auto-generated catch block
				System.out.println(ioe.getLocalizedMessage());
				ioe.printStackTrace();
			}
		}
		if (path.length() != 0) {
			try {
				url = new URL("file:" + file.toPath().toString());
				System.out.println(url.toString());
				manifest = new Manifest(url.openStream());
				System.out.println(manifest.toString());
			} catch (MalformedURLException ue) {
				// TODO Auto-generated catch block
				System.out.println(ue.getLocalizedMessage());
				ue.printStackTrace();
			} catch (IOException ioe) {
				// TODO Auto-generated catch block
				System.out.println(ioe.getLocalizedMessage());
				ioe.printStackTrace();
			}
		}
		
		if (manifest == null) {
			_version = "0.0.0";
			return;
		}
		attr = manifest.getMainAttributes();
		_version = attr.getValue("Specification-Version");
		System.out.println("Specification Version: " + _version);
	}
	
	public static String getFont() {
		if (_font == "none") {
			_font = "";
			GraphicsEnvironment e = GraphicsEnvironment.getLocalGraphicsEnvironment();
			for (String fName : e.getAvailableFontFamilyNames()) {
				if (fName.equals("Helvetica Neue")) {
					_font = fName;
					break;
				}
				if (fName.equals("Helvetica")) {
					_font = fName;
					break;
				}
				if (fName.equals("Arial")) {
					_font = fName;
					break;
				}
				if (fName.equals("Verdana")) {
					_font = fName;
					break;
				}
			}
		}
		return _font;
	}

	public static String getApplicationVersion() {
		return _version;
	}
}