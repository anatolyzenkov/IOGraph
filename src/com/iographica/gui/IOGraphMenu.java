package com.iographica.gui;

import java.awt.CheckboxMenuItem;
import java.awt.Menu;
import java.awt.MenuBar;
import java.awt.MenuItem;
import java.awt.MenuShortcut;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.awt.event.KeyEvent;
import java.util.ArrayList;

import com.iographica.core.Data;
import com.iographica.core.IOGraph;
import com.iographica.core.WebSurfer;
import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;

public class IOGraphMenu extends MenuBar implements IEventDispatcher, IEventHandler {

	private static final long serialVersionUID = 8783422766432999905L;
	private AboutDialog _aboutDialog;
	private ArrayList<IEventHandler> _eventHandlers;
	private MenuItem _checkForUpdateMenuItem;
	private CheckboxMenuItem _checkForUpdateAutomaticalyMenuItem;
	private MenuItem _saveImageMenuItem;
	private MenuItem _saveCSVMenuItem;
	private MenuItem _resetMenuItem;
	private MenuItem _recordPauseMenuItem;
	private CheckboxMenuItem _ignoreMouseStopsMenuItem;
	private CheckboxMenuItem _useMultiplyMonitorsMenuItem;
	private CheckboxMenuItem _useColorfulSchemeMenuItem;
	private CheckboxMenuItem _useScreenshotMenuItem;
	private MenuItem _updateScreenshot;

	public IOGraphMenu() {
		Menu m;
		MenuItem mi;

		m = this.add(new Menu("File"));
		_saveImageMenuItem = m.add(new MenuItem("Save Image…", new MenuShortcut(KeyEvent.VK_S)));
		_saveImageMenuItem.setEnabled(false);
		_saveImageMenuItem.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				dispatchEvent(Data.SAVE_IMAGE);
			}
		});
		_saveCSVMenuItem = m.add(new MenuItem("Save Raw Data…"));
		_saveCSVMenuItem.setEnabled(false);
		_saveCSVMenuItem.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				dispatchEvent(Data.SAVE_CSV);
			}
		});
		
		if (!Data.isOSX) {
			m.addSeparator();
			mi = m.add(new MenuItem("Exit"));
			mi.addActionListener(new java.awt.event.ActionListener() {
				public void actionPerformed(java.awt.event.ActionEvent e) {
					dispatchEvent(Data.SYSTEM_QUIT_REQUESTED);
				}
			});
		}

		m = this.add(new Menu("Tracking"));
		_recordPauseMenuItem = m.add(new MenuItem("Start", new MenuShortcut(KeyEvent.VK_R)));
		_recordPauseMenuItem.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				Data.mouseTrackRecording = !Data.mouseTrackRecording;
				if (Data.mouseTrackRecording) {
					dispatchEvent(Data.START_DRAW);
				} else {
					dispatchEvent(Data.STOP_DRAW);
				}
			}
		});

		_resetMenuItem = m.add(new MenuItem("Reset", new MenuShortcut(KeyEvent.VK_N)));
		_resetMenuItem.setEnabled(false);
		_resetMenuItem.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				if (IOGraph.resetConfirmation()) dispatchEvent(Data.RESET);
			}
		});

		m = this.add(new Menu("Settings"));
		
		_useColorfulSchemeMenuItem = new CheckboxMenuItem("Use Colourful Scheme");
		_useColorfulSchemeMenuItem.setShortcut(new MenuShortcut(KeyEvent.VK_F));
		m.add(_useColorfulSchemeMenuItem);
		_useColorfulSchemeMenuItem.setState(Data.prefs.getBoolean(Data.USE_COLOR_SCHEME, false));
		_useColorfulSchemeMenuItem.addItemListener(new ItemListener() {
			public void itemStateChanged(ItemEvent e) {
				if (_useColorfulSchemeMenuItem.getState() != Data.prefs.getBoolean(Data.USE_COLOR_SCHEME, false)) {
					Data.requestedColorfulSchemeUsage = _useColorfulSchemeMenuItem.getState();
					dispatchEvent(Data.COLORFUL_SCHEME_USAGE_CHANGING_REQUEST);
					boolean b = Data.prefs.getBoolean(Data.USE_COLOR_SCHEME, false);
					if (_useColorfulSchemeMenuItem.getState() != b) {
						_useColorfulSchemeMenuItem.setState(b);
					}
				}
			}
		});
		
		m.addSeparator();
		
		_ignoreMouseStopsMenuItem = new CheckboxMenuItem("Ignore Mouse Stops");
		_ignoreMouseStopsMenuItem.setShortcut(new MenuShortcut(KeyEvent.VK_I));
		m.add(_ignoreMouseStopsMenuItem);
		_ignoreMouseStopsMenuItem.setState(Data.prefs.getBoolean(Data.IGNORE_MOUSE_STOPS, false));
		_ignoreMouseStopsMenuItem.addItemListener(new ItemListener() {
			public void itemStateChanged(ItemEvent e) {
				if (_ignoreMouseStopsMenuItem.getState() != Data.prefs.getBoolean(Data.IGNORE_MOUSE_STOPS, false)) dispatchEvent(Data.IGNORE_MOUSE_STOPS_CHANGED);
			}
		});
		
		_useScreenshotMenuItem = new CheckboxMenuItem("Use Desktop");
		_useScreenshotMenuItem.setShortcut(new MenuShortcut(KeyEvent.VK_D));
		m.add(_useScreenshotMenuItem);
		_useScreenshotMenuItem.addItemListener(new ItemListener() {
			public void itemStateChanged(ItemEvent e) {
				if (_useScreenshotMenuItem.getState() != Data.useScreenshot) dispatchEvent(Data.BACKGROUND_USAGE_CHANGE_REQUEST);
			}
		});
		
		_updateScreenshot = m.add(new MenuItem("Take New Screenshot"));
		_updateScreenshot.setShortcut(new MenuShortcut(KeyEvent.VK_N, true));
		_updateScreenshot.setEnabled(false);
		_updateScreenshot.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent arg0) {
				_updateScreenshot.setEnabled(false);
				dispatchEvent(Data.UPDATE_BACKGROUND);
			}
		});
		m.addSeparator();
		
		_useMultiplyMonitorsMenuItem = new CheckboxMenuItem("Use Multiple Monitors");
		_useMultiplyMonitorsMenuItem.setShortcut(new MenuShortcut(KeyEvent.VK_M));
		m.add(_useMultiplyMonitorsMenuItem);
		_useMultiplyMonitorsMenuItem.setEnabled(Data.moreThanOneMonitor);
		_useMultiplyMonitorsMenuItem.setState(Data.prefs.getBoolean(Data.USE_MULTIPLE_MONITORS, true));
		_useMultiplyMonitorsMenuItem.addItemListener(new ItemListener() {
			public void itemStateChanged(ItemEvent e) {
				if (_useMultiplyMonitorsMenuItem.getState() != Data.prefs.getBoolean(Data.USE_MULTIPLE_MONITORS, false)) {
					Data.requestedMultiMonitorUsage = _useMultiplyMonitorsMenuItem.getState();
					dispatchEvent(Data.MULTI_MONITOR_USAGE_CHANGING_REQUEST);
					boolean b = Data.prefs.getBoolean(Data.USE_MULTIPLE_MONITORS, false);
					if (_useMultiplyMonitorsMenuItem.getState() != b) {
						_useMultiplyMonitorsMenuItem.setState(b);
					}
				}
			}
		});

		m = this.add(new Menu("Help"));
		mi = m.add(new MenuItem("Get Source Code from GitHub…"));
		mi.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				WebSurfer.get(Data.GIT_REPO_URL);
			}
		});
		if (!Data.isOSX) {
			m.addSeparator();
			mi = m.add(new MenuItem("About IOGraph"));
			mi.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent e) {
					showAboutDialog();
				}
			});
		}
		m.addSeparator();
		_checkForUpdateMenuItem = m.add(new MenuItem("Check for Updates"));
		_checkForUpdateMenuItem.setEnabled(false);
		_checkForUpdateMenuItem.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				_checkForUpdateMenuItem.setEnabled(false);
				Data.isCheckingForUpdates = true;
				dispatchEvent(Data.CHECK_FOR_UPDATES);
			}
		});
		_checkForUpdateAutomaticalyMenuItem = new CheckboxMenuItem("Check for Updates Automaticaly", Data.prefs.getBoolean(Data.AUTOMATIC_UPDATE, false));
		_checkForUpdateAutomaticalyMenuItem.addItemListener(new ItemListener() {
			public void itemStateChanged(ItemEvent e) {
				Data.prefs.putBoolean(Data.AUTOMATIC_UPDATE, _checkForUpdateAutomaticalyMenuItem.getState());
			}
		});
		m.add(_checkForUpdateAutomaticalyMenuItem);
		m.addSeparator();
		mi = m.add(new MenuItem("Join Our Facebook Community…"));
		mi.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				WebSurfer.get(Data.FACEBOOK_PAGE_URL);
			}
		});
		mi = m.add(new MenuItem("Visit IOGraphica's Website…"));
		mi.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				WebSurfer.get(Data.WEBSITE_URL);
			}
		});
	}

	public void showAboutDialog() {
		if (_aboutDialog == null) {
			_aboutDialog = new AboutDialog(Data.mainFrame);
		}
		_aboutDialog.setVisible(true);
	}

	public void osxOnExit() {
		dispatchEvent(Data.SYSTEM_QUIT_REQUESTED);
	}

	private void dispatchEvent(int type) {
		if (_eventHandlers != null) {
			final IOEvent event = new IOEvent(type, this);
			for (IEventHandler handler : _eventHandlers) {
				handler.onEvent(event);
			}
		}
	}

	public void addEventHandler(IEventHandler handler) {
		if (_eventHandlers == null) {
			_eventHandlers = new ArrayList<IEventHandler>();
		}
		for (IEventHandler handler2 : _eventHandlers) if (handler2.equals(handler)) return;
		_eventHandlers.add(handler);
	}

	public void onEvent(IOEvent event) {
		switch (event.type) {
		case Data.SHOW_ABOUT:
			showAboutDialog();
			break;
		case Data.SYSTEM_QUIT_REQUESTED:
			dispatchEvent(Data.SYSTEM_QUIT_REQUESTED);
			break;
		case Data.CHECK_FOR_UPDATES_COMPLETE:
			Data.isCheckingForUpdates = false;
			_checkForUpdateMenuItem.setEnabled(true);
			break;
		case Data.AUTO_CHECK_FOR_UPDATES_CHANGED:
			_checkForUpdateAutomaticalyMenuItem.setState(Data.prefs.getBoolean(Data.AUTOMATIC_UPDATE, false));
			break;
		case Data.START_DRAW:
			_saveImageMenuItem.setEnabled(true);
			_saveCSVMenuItem.setEnabled(true);
			_recordPauseMenuItem.setLabel("Pause");
			break;
		case Data.STOP_DRAW:
			if (Data.trackingTime == 0 && !Data.mouseTrackRecording) {
				_recordPauseMenuItem.setLabel("Start");
			} else {
				_recordPauseMenuItem.setLabel("Resume");
			}
			break;
		case Data.RESET:
			if (!Data.mouseTrackRecording) _saveImageMenuItem.setEnabled(false);
			if (!Data.mouseTrackRecording) _saveCSVMenuItem.setEnabled(false);
			if (!Data.mouseTrackRecording) _resetMenuItem.setEnabled(false);
			break;
		case Data.RESET_ENABLED:
			if (!_resetMenuItem.isEnabled()) _resetMenuItem.setEnabled(true);
			break;
		case Data.RESET_DISABLED:
			if (_resetMenuItem.isEnabled()) _resetMenuItem.setEnabled(false);
			break;
		case Data.IGNORE_MOUSE_STOPS_CHANGED:
			boolean b = Data.prefs.getBoolean(Data.IGNORE_MOUSE_STOPS, false);
			if (b != _ignoreMouseStopsMenuItem.getState()) _ignoreMouseStopsMenuItem.setState(b);
			break;
		case Data.MULTI_MONITOR_USAGE_CHANGED:
			b = Data.prefs.getBoolean(Data.USE_MULTIPLE_MONITORS, false);
			if (b != _useMultiplyMonitorsMenuItem.getState()) _useMultiplyMonitorsMenuItem.setState(b);
			break;
		case Data.COLOR_SCHEME_CHANGED:
			b = Data.prefs.getBoolean(Data.USE_COLOR_SCHEME, false);
			if (b != _useColorfulSchemeMenuItem.getState()) _useColorfulSchemeMenuItem.setState(b);
			break;
		case Data.BACKGROUND_USAGE_CHANGED:
			if (Data.useScreenshot != _useScreenshotMenuItem.getState()) _useScreenshotMenuItem.setState(Data.useScreenshot);
			_updateScreenshot.setEnabled(Data.useScreenshot);
			break;
		case Data.BACKGROUND_IS_UP_TO_DATE:
			_updateScreenshot.setEnabled(true);
			break;
		default:
			break;
		}
	}
}