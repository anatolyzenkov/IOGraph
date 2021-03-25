package com.iographica.gui;

import java.awt.AWTException;
import java.awt.CheckboxMenuItem;
import java.awt.Menu;
import java.awt.MenuItem;
import java.awt.MenuShortcut;
import java.awt.PopupMenu;
import java.awt.SystemTray;
import java.awt.TrayIcon;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.awt.event.KeyEvent;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.util.ArrayList;

import javax.swing.ImageIcon;

import com.iographica.core.Data;
import com.iographica.core.IOGraph;
import com.iographica.core.WebSurfer;
import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;

public class IOGraphTrayIcon implements IEventDispatcher, IEventHandler {
	TrayIcon _trayIcon = null;
	MainFrame _frame = null;
	private ArrayList<IEventHandler> _eventHandlers;
	private Boolean _settingsVisible = false;
	private MenuItem _saveImage;
	private MenuItem _saveCVS;
	private MenuItem _trackingToggle;
	private MenuItem _resetMenuItem;
	private MenuItem _settingsItem;
	private MenuItem _checkForUpdateMenuItem;
	private CheckboxMenuItem _checkForUpdateAutomaticalyMenuItem;
	private AboutDialog _aboutDialog;

	public IOGraphTrayIcon(MainFrame frame) {
        if (Data.isTrayGUI) {
    		_frame = frame;
            SystemTray tray = SystemTray.getSystemTray();
            ImageIcon icon = IOGraph.getIcon("MenuBarIconRecord.png");
            
            PopupMenu popup = new PopupMenu();
            
            
            _trackingToggle = popup.add(new MenuItem("Start", new MenuShortcut(KeyEvent.VK_R)));
    		_trackingToggle.addActionListener(new ActionListener() {
    			public void actionPerformed(ActionEvent e) {
    				Data.mouseTrackRecording = !Data.mouseTrackRecording;
    				if (Data.mouseTrackRecording) {
    					dispatchEvent(Data.START_DRAW);
    				} else {
    					dispatchEvent(Data.STOP_DRAW);
    				}
    			}
    		});

    		_resetMenuItem = popup.add(new MenuItem("Reset", new MenuShortcut(KeyEvent.VK_N)));
    		_resetMenuItem.setEnabled(false);
    		_resetMenuItem.addActionListener(new ActionListener() {
    			public void actionPerformed(ActionEvent e) {
    				if (IOGraph.resetConfirmation()) dispatchEvent(Data.RESET);
    			}
    		});
            
    		popup.addSeparator();
            _saveImage = popup.add(new MenuItem("Save...", new MenuShortcut(KeyEvent.VK_S)));
            _saveImage.setEnabled(false);
            _saveImage.addActionListener(new ActionListener() {
                public void actionPerformed(ActionEvent e) {
                	dispatchEvent(Data.SAVE_IMAGE);
                }
        	});
            
            popup.addSeparator();
            
            _settingsItem = popup.add(new MenuItem("Show Settings"));
            _settingsItem.addActionListener(new ActionListener() {
                public void actionPerformed(ActionEvent e) {
                	if (_settingsVisible) {
                		_settingsVisible = false;
                		dispatchEvent(Data.CLOSE_CONTROLS);
                		_settingsItem.setLabel("Show Settings");
                	} else {
                		_settingsVisible = true;
                		dispatchEvent(Data.OPEN_CONTROLS);
                		_settingsItem.setLabel("Hide Settings");
                	}
                }
        	});
            
            Menu sectionsMenu = new Menu("More");
            popup.add(sectionsMenu);
            MenuItem mi = null;
            
            _saveCVS = sectionsMenu.add(new MenuItem("Save Raw Data..."));
            _saveCVS.setEnabled(false);
            _saveCVS.addActionListener(new ActionListener() {
                public void actionPerformed(ActionEvent e) {
                	dispatchEvent(Data.SAVE_CSV);
                }
        	});
            
    		sectionsMenu.addSeparator();
    		
    		_checkForUpdateMenuItem = sectionsMenu.add(new MenuItem("Check for Updates"));
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
    		sectionsMenu.add(_checkForUpdateAutomaticalyMenuItem);
    		sectionsMenu.addSeparator();
    		
            mi = sectionsMenu.add(new MenuItem("Get Source Code from GitHub"));
    		mi.addActionListener(new ActionListener() {
    			public void actionPerformed(ActionEvent e) {
    				WebSurfer.get(Data.GIT_REPO_URL);
    			}
    		});
    		mi = sectionsMenu.add(new MenuItem("Join Our Facebook Community"));
    		mi.addActionListener(new ActionListener() {
    			public void actionPerformed(ActionEvent e) {
    				WebSurfer.get(Data.FACEBOOK_PAGE_URL);
    			}
    		});
    		mi = sectionsMenu.add(new MenuItem("Visit IOGraphica's Website"));
    		mi.addActionListener(new ActionListener() {
    			public void actionPerformed(ActionEvent e) {
    				WebSurfer.get(Data.WEBSITE_URL);
    			}
    		});
            sectionsMenu.addSeparator();
			mi = sectionsMenu.add(new MenuItem("About IOGraph"));
			mi.addActionListener(new ActionListener() {
				public void actionPerformed(ActionEvent e) {
					showAboutDialog();
				}
			});
            
            popup.addSeparator();
            MenuItem quitItem = popup.add(new MenuItem("Quit"));
            quitItem.addActionListener(new ActionListener() {
                public void actionPerformed(ActionEvent e) {
                	dispatchEvent(Data.SYSTEM_QUIT_REQUESTED);
                }
        	});
            
            _trayIcon = new TrayIcon(icon.getImage(), Data.APPLICATION_NAME, popup);
            TryMouseListener mouseListener = new TryMouseListener();
            _trayIcon.addMouseListener(mouseListener);
            try {
                tray.add(_trayIcon);
            } catch (AWTException e) {
                System.err.println(e);
            }
        }
        
	}
	public void showAboutDialog() {
		if (_aboutDialog == null) {
			_aboutDialog = new AboutDialog(Data.mainFrame);
		}
		_aboutDialog.setVisible(true);
	}
	@Override
	public void onEvent(IOEvent event) {
		switch (event.type) {
		case Data.CHECK_FOR_UPDATES_COMPLETE:
			Data.isCheckingForUpdates = false;
			_checkForUpdateMenuItem.setEnabled(true);
			break;
		case Data.AUTO_CHECK_FOR_UPDATES_CHANGED:
			_checkForUpdateAutomaticalyMenuItem.setState(Data.prefs.getBoolean(Data.AUTOMATIC_UPDATE, false));
			break;
		case Data.CLOSE_CONTROLS:
			_settingsVisible = false;
			_settingsItem.setLabel("Show Settings");
			break;
		case Data.OPEN_CONTROLS:
			_settingsVisible = true;
			_settingsItem.setLabel("Hide Settings");
			break;
		case Data.STOP_DRAW:
			if (Data.trackingTime == 0 && !Data.mouseTrackRecording) {
				_trackingToggle.setLabel("Start");
			} else {
				_trackingToggle.setLabel("Resume");
			}
			break;
		case Data.RESET:
			if (!Data.mouseTrackRecording) {
				_trackingToggle.setLabel("Start");
				_saveImage.setEnabled(false);
				_saveCVS.setEnabled(false);
				_resetMenuItem.setEnabled(false);
			}
			break;
		case Data.RESET_ENABLED:
			_resetMenuItem.setEnabled(true);
			break;
		case Data.RESET_DISABLED:
			_resetMenuItem.setEnabled(false);
			break;
		case Data.START_DRAW:
			_saveCVS.setEnabled(true);
			_saveImage.setEnabled(true);
			_trackingToggle.setLabel("Pause");
			break;
		default:
			break;
		}
	}
	@Override
	public void addEventHandler(IEventHandler handler) {
		if (_eventHandlers == null) {
			_eventHandlers = new ArrayList<IEventHandler>();
		}
		for (IEventHandler handler2 : _eventHandlers) if (handler2.equals(handler)) return;
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
	
	public class TryMouseListener implements MouseListener {
		@Override
		public void mouseClicked(MouseEvent e) {
//			System.out.println(e);
		}

		@Override
		public void mousePressed(MouseEvent e) {
//			 System.out.println(e);
			if (e.getButton() == MouseEvent.BUTTON1) {
				_frame.showOnTop();
			};
			if (e.getButton() == MouseEvent.BUTTON3) {
			};
		}

		@Override
		public void mouseReleased(MouseEvent e) {
		}

		@Override
		public void mouseEntered(MouseEvent e) {
		}

		@Override
		public void mouseExited(MouseEvent e) {
		}
	}

}