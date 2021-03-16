package com.iographica.core;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.URL;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.regex.Pattern;

import javax.swing.JOptionPane;

import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;
import com.iographica.gui.UpdateConsoleFrame;

public class UpdateChecker extends Object implements IEventDispatcher, IEventHandler {
	private ArrayList<IEventHandler> _eventHandlers;
	private UpdateConsoleFrame _updateConsoleFrame;

	public UpdateChecker() {
		_updateConsoleFrame = new UpdateConsoleFrame();
		_updateConsoleFrame.addEventHandler(this);
	}

	public void check() {
		Thread t = new Thread() {
			public void run() {
				String serverVersion = "";
				if (!Data.isCheckingForUpdates && !Data.prefs.getBoolean(Data.AUTOMATIC_UPDATE, true)) {
					dispatchEvent(Data.CHECK_FOR_UPDATES_COMPLETE);
					return;
				}
				
				if (Data.isCheckingForUpdates) _updateConsoleFrame.setVisible(true);
				try {
					URL iographica = new URL(Data.UPDATE_URL);
					URLConnection connection = iographica.openConnection();
					connection.setDoOutput(true);

					OutputStreamWriter out = new OutputStreamWriter(connection.getOutputStream());
					out.write("application=" + Data.APPLICATION_NAME);
					out.write("version=" + Data.getApplicationVersion());
					out.close();

					BufferedReader in = new BufferedReader(new InputStreamReader(iographica.openStream()));
					String inputLine;
					while ((inputLine = in.readLine()) != null) {
						serverVersion += inputLine;
					}
					in.close();
				} catch (Exception e) {
					System.out.println("Can't get update url");
					if (Data.isCheckingForUpdates) {
						_updateConsoleFrame.showError();
					} else {
						dispatchEvent(Data.CHECK_FOR_UPDATES_COMPLETE);
					}
					return;
				}

				if (!Pattern.matches("([0-9]+\\.)+[0-9]+", serverVersion)) {
					if (Data.isCheckingForUpdates) {
						_updateConsoleFrame.showError();
					} else {					
						dispatchEvent(Data.CHECK_FOR_UPDATES_COMPLETE);
					}
					return;
				}
				if (!Pattern.matches("([0-9]+\\.)+[0-9]+", Data.getApplicationVersion())) {
					if (Data.isCheckingForUpdates) {
						_updateConsoleFrame.showError();
					} else {					
						dispatchEvent(Data.CHECK_FOR_UPDATES_COMPLETE);
					}
					return;
				}
				String[] server = serverVersion.split("\\.");
				String[] local = Data.getApplicationVersion().split("\\.");
				boolean upToDate = true;
				for (int i = 0; i < server.length; i++) {
					int srvr = Integer.parseInt(server[i]);
					int locl = i < local.length ? Integer.parseInt(local[i]) : 0;
					if (locl < srvr) {
						upToDate = false;
						break;
					}
					if (locl > srvr) break;
				}
				if (upToDate) {
					if (Data.isCheckingForUpdates) {
						_updateConsoleFrame.upToDate();
					} else {					
						dispatchEvent(Data.CHECK_FOR_UPDATES_COMPLETE);
					}
					return;
				}
				_updateConsoleFrame.setVisible(false);

				String header = "Updates Are Avaliable";
				String message = "There is a new version available for download!\n" + "Would you like to visit IOGraphica's website\n" + "and get a brand new IOGraph?";

				Object[] options = { "Yes", "Later", "No" };
				int cd = JOptionPane.showOptionDialog(null, message, header, JOptionPane.YES_NO_CANCEL_OPTION, JOptionPane.QUESTION_MESSAGE, IOGraph.getIcon("UpdateDialogIcon.png"), options, options[0]);
				dispatchEvent(Data.CHECK_FOR_UPDATES_COMPLETE);
				if (cd == JOptionPane.CANCEL_OPTION) {
					Data.prefs.putBoolean(Data.AUTOMATIC_UPDATE, false);
					dispatchEvent(Data.AUTO_CHECK_FOR_UPDATES_CHANGED);
					return;
				}
				if (cd != JOptionPane.YES_OPTION) {
					return;
				}
				WebSurfer.get(Data.WEBSITE_URL);
			}
		};
		t.start();
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
		_eventHandlers.add(handler);
	}

	public void onEvent(IOEvent event) {
		switch (event.type) {
		case Data.CHECK_FOR_UPDATES_COMPLETE:
			dispatchEvent(Data.CHECK_FOR_UPDATES_COMPLETE);
			break;
		default:
			break;
		}
	}
}
