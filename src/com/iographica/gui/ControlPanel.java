package com.iographica.gui;

import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.GridLayout;
import java.util.ArrayList;

import javax.swing.BorderFactory;
import javax.swing.JCheckBox;
import javax.swing.JPanel;
import javax.swing.SwingConstants;

import com.iographica.core.Data;
import com.iographica.core.IOGraph;
import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;

public class ControlPanel extends JPanel implements IEventDispatcher, IEventHandler {

	private static final long serialVersionUID = 1L;
	private JCheckBox _ignoreMousePauses = null;
	private JCheckBox _multipleMonitors = null;
	private JCheckBox _useBackground = null;
	private JCheckBox _updateBackground = null;
	private JPanel _screenshotPanel;
	private ArrayList<IEventHandler> _eventHandlers;
	private JCheckBox _colorSceme;

	public ControlPanel() {
		super();
		initialize();
	}

	private void initialize() {
		GridLayout gridLayout = new GridLayout();
		gridLayout.setRows(2);
		gridLayout.setColumns(2);
		this.setLayout(gridLayout);
		this.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 0));
		this.add(get_recordMouseStops(), null);
		this.add(get_screenshotPanel(), null);
		this.add(get_multipleMonitors(), null);
		this.add(get_colorScheme(), null);
		this.setSize(Data.MAIN_FRAME_WIDTH - 20, Data.PANEL_HEIGHT);
		this.setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH - 20, Data.PANEL_HEIGHT));
	}

	private JCheckBox get_recordMouseStops() {
		if (_ignoreMousePauses == null) {
			_ignoreMousePauses = new JCheckBox();
			_ignoreMousePauses.setText("Ignore Mouse Stops");
			_ignoreMousePauses.setToolTipText("Do not draw circles");
			_ignoreMousePauses.setHorizontalAlignment(SwingConstants.LEFT);
			setLook(_ignoreMousePauses, false);
			_ignoreMousePauses.setSelected(Data.prefs.getBoolean(Data.IGNORE_MOUSE_STOPS, false));
			_ignoreMousePauses.setFont(new Font(_ignoreMousePauses.getFont().getFontName(), Font.PLAIN, 13));
			_ignoreMousePauses.setForeground(Data.TEXT_COLOR);
			_ignoreMousePauses.addItemListener(new java.awt.event.ItemListener() {
				public void itemStateChanged(java.awt.event.ItemEvent e) {
					if (Data.prefs.getBoolean(Data.IGNORE_MOUSE_STOPS, false) != _ignoreMousePauses.isSelected()) dispatchEvent(Data.IGNORE_MOUSE_STOPS_CHANGED);
				}
			});
		}
		return _ignoreMousePauses;
	}

	private JCheckBox get_multipleMonitors() {
		if (_multipleMonitors == null) {
			_multipleMonitors = new JCheckBox();
			_multipleMonitors.setEnabled(Data.moreThanOneMonitor);
			setLook(_multipleMonitors, false);
			_multipleMonitors.setFont(new Font(_multipleMonitors.getFont().getFontName(), Font.PLAIN, 13));
			_multipleMonitors.setForeground(Data.TEXT_COLOR);
			_multipleMonitors.setSelected(Data.prefs.getBoolean(Data.USE_MULTIPLE_MONITORS, true));
			_multipleMonitors.setText("Use Multiple Monitors");
			_multipleMonitors.setHorizontalAlignment(SwingConstants.LEFT);
			_multipleMonitors.setToolTipText("Use multiple monitors");
			_multipleMonitors.addItemListener(new java.awt.event.ItemListener() {
				public void itemStateChanged(java.awt.event.ItemEvent e) {
					if (_multipleMonitors.isSelected() != Data.prefs.getBoolean(Data.USE_MULTIPLE_MONITORS, false)) {
						Data.requestedMultiMonitorUsage = _multipleMonitors.isSelected();
						dispatchEvent(Data.MULTI_MONITOR_USAGE_CHANGING_REQUEST);
						boolean b = Data.prefs.getBoolean(Data.USE_MULTIPLE_MONITORS, false);
						if (_multipleMonitors.isSelected() != b) _multipleMonitors.setSelected(b);
					}
				}
			});
		}
		return _multipleMonitors;
	}

	private JPanel get_screenshotPanel() {
		if (_screenshotPanel == null) {
			_screenshotPanel = new JPanel();
			FlowLayout layout = new FlowLayout(FlowLayout.LEFT, 0, 0);
			_screenshotPanel.setLayout(layout);
			_screenshotPanel.add(get_useScreenshot());
			_screenshotPanel.add(get_updateScreenshot());
			_screenshotPanel.setOpaque(false);
		}
		return _screenshotPanel;
	}

	private JCheckBox get_useScreenshot() {
		if (_useBackground == null) {
			_useBackground = new JCheckBox();
			_useBackground.setText("Use Desktop");
			_useBackground.setToolTipText("Use desktop as background");
			setLook(_useBackground, false);
			_useBackground.setFont(new Font(_useBackground.getFont().getFontName(), Font.PLAIN, 13));
			_useBackground.setForeground(Data.TEXT_COLOR);
			_useBackground.addItemListener(new java.awt.event.ItemListener() {
				public void itemStateChanged(java.awt.event.ItemEvent e) {
					if (_useBackground.isSelected() != Data.useScreenshot) dispatchEvent(Data.BACKGROUND_USAGE_CHANGE_REQUEST);
				}
			});
		}
		return _useBackground;
	}

	private JCheckBox get_colorScheme() {
		if (_colorSceme == null) {
			_colorSceme = new JCheckBox();
			_colorSceme.setFont(new Font(_multipleMonitors.getFont().getFontName(), Font.PLAIN, 13));
			_colorSceme.setForeground(Data.TEXT_COLOR);
			_colorSceme.setSelected(Data.prefs.getBoolean(Data.USE_COLOR_SCHEME, false));
			_colorSceme.setText("Use Colourful Scheme");
			_colorSceme.setToolTipText("Use colorful scheme instead black and white one");
			setLook(_colorSceme, false);
			_colorSceme.addItemListener(new java.awt.event.ItemListener() {
				public void itemStateChanged(java.awt.event.ItemEvent e) {
					if (_colorSceme.isSelected() != Data.prefs.getBoolean(Data.USE_COLOR_SCHEME, false)) {
						Data.requestedColorfulSchemeUsage = _colorSceme.isSelected();
						dispatchEvent(Data.COLORFUL_SCHEME_USAGE_CHANGING_REQUEST);
						boolean b = Data.prefs.getBoolean(Data.USE_COLOR_SCHEME, false);
						if (_colorSceme.isSelected() != b) _colorSceme.setSelected(b);
					}
				}
			});
		}
		return _colorSceme;
	}

	private void setLook(JCheckBox b, boolean c) {
		b.setOpaque(false);
	}

	private JCheckBox get_updateScreenshot() {
		if (_updateBackground == null) {
			_updateBackground = new JCheckBox();
			_updateBackground.setToolTipText("Take new screenshot of your desktop");
			_updateBackground.setIcon(IOGraph.getIcon("UpdateDesktopBtn.png"));
			_updateBackground.setPressedIcon(IOGraph.getIcon("UpdateDesktopPressedBtn.png"));
			_updateBackground.setDisabledIcon(IOGraph.getIcon("UpdateDesktopDisabledBtn.png"));
			_updateBackground.setVisible(false);
			_updateBackground.setOpaque(false);
			_updateBackground.setName("_updateBackground");
			_updateBackground.addItemListener(new java.awt.event.ItemListener() {
				public void itemStateChanged(java.awt.event.ItemEvent e) {
					dispatchEvent(Data.UPDATE_BACKGROUND);
				}
			});
		}
		return _updateBackground;
	}

	public void addEventHandler(IEventHandler handler) {
		if (_eventHandlers == null) {
			_eventHandlers = new ArrayList<IEventHandler>();
		}
		for (IEventHandler handler2 : _eventHandlers)
			if (handler2.equals(handler)) return;
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

	public void onEvent(IOEvent event) {
		boolean b;
		switch (event.type) {
		case Data.IGNORE_MOUSE_STOPS_CHANGED:
			b = Data.prefs.getBoolean(Data.IGNORE_MOUSE_STOPS, false);
			if (b != _ignoreMousePauses.isSelected()) _ignoreMousePauses.setSelected(b);
			break;
		case Data.MULTI_MONITOR_USAGE_CHANGED:
			b = Data.prefs.getBoolean(Data.USE_MULTIPLE_MONITORS, false);
			if (b != _multipleMonitors.isSelected()) _multipleMonitors.setSelected(b);
			break;
		case Data.COLOR_SCHEME_CHANGED:
			b = Data.prefs.getBoolean(Data.USE_COLOR_SCHEME, false);
			if (b != _colorSceme.isSelected()) _colorSceme.setSelected(b);
			break;
		case Data.BACKGROUND_USAGE_CHANGED:
			if (Data.useScreenshot != _useBackground.isSelected()) _useBackground.setSelected(Data.useScreenshot);
			_updateBackground.setVisible(Data.useScreenshot);
			break;
		default:
			break;
		}
	}
}