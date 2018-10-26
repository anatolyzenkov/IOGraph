package com.iographica.gui;

import java.awt.GridBagLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;

import javax.swing.ImageIcon;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.Timer;

import com.iographica.core.Data;
import com.iographica.core.IOGraph;
import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;

public class UpdateConsoleFrame extends JFrame implements IEventDispatcher {
	private static final long serialVersionUID = 1L;
	private JLabel _label;
	private ImageIcon _loading;
	private ArrayList<IEventHandler> _eventHandlers;
	private Timer _timer;

	public UpdateConsoleFrame() {
		setSize(300, 100);
		setResizable(false);
		setTitle("Updates");
		setDefaultCloseOperation(HIDE_ON_CLOSE);
		GridBagLayout layout = new GridBagLayout();
		setLayout(layout);
		_loading = IOGraph.getIcon("Loading.gif");
		_label = new JLabel("", null, JLabel.CENTER);
		_label.setOpaque(false);
		add(_label);
		_timer = new Timer(3000, new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				setVisible(false);
				dispatchEvent(Data.CHECK_FOR_UPDATES_COMPLETE);
				_timer.stop();
			}
		});
	}

	@Override
	public void setVisible(boolean b) {
		_label.setText("Checking for Updates...");
		_label.setIcon(_loading);
		setLocation((int) (Data.mainFrame.getX() + (Data.mainFrame.getWidth() - this.getWidth()) * .5), (int) (Data.mainFrame.getY() + (Data.mainFrame.getHeight() - this.getHeight()) * .5));
		super.setVisible(b);
	}

	public void setText(String s) {
		_label.setIcon(null);
		_label.setText(s);
		validate();
		_timer.start();
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

	public void showError() {
		setText("Can't check for update right now.");
	}

	public void upToDate() {
		setText("Your IOGraph version is up to date.");
	}
}