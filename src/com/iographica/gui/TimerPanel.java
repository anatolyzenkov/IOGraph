package com.iographica.gui;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;
import java.awt.Rectangle;
import java.net.URL;
import java.util.ArrayList;

import javax.swing.BorderFactory;
import javax.swing.ImageIcon;
import javax.swing.JCheckBox;
import javax.swing.JLabel;
import javax.swing.JPanel;

import com.iographica.core.Data;
import com.iographica.core.IOGraph;
import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;


public class TimerPanel extends JPanel implements IEventHandler, IEventDispatcher {

	private static final long serialVersionUID = 1L;
	private JLabel _total = null;
	private JLabel _preiod = null;
	private Color _color;
	private JCheckBox _resetBox = null;
	private ArrayList<IEventHandler> _eventHandlers;

	/**
	 * This is the default constructor
	 */
	public TimerPanel(Color color) {
		super();
		_color = color;
		initialize();
	}

	/**
	 * This method initializes this
	 * 
	 * @return void
	 */
	private void initialize() {
		_preiod = new JLabel();
		_preiod.setFont(new Font(_preiod.getFont().getFontName(), Font.PLAIN, 12));
		_preiod.setText("Time Period");
		_preiod.setOpaque(false);
		_preiod.setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH, 20));
		_preiod.setBounds(new Rectangle(0, 41, 70, 15));
		_preiod.setForeground(_color);

		_total = new JLabel();
		_total.setFont(new Font(_total.getFont().getFontName(), Font.PLAIN, 30));
		_total.setText("Total Time");
		_total.setOpaque(false);
		_total.setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH, 36));
		_total.setForeground(_color);

		this.setSize(465, 66);
		this.setSize(Data.MAIN_FRAME_WIDTH, Data.PANEL_HEIGHT);
		this.setLayout(null);
		this.setBorder(BorderFactory.createEmptyBorder(5, 0, 0, 0));
		this.setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH, Data.PANEL_HEIGHT));
		this.setVisible(false);
		this.add(_total, null);
		this.add(_preiod, null);
		this.add(get_resetBox(), null);
	}

	public void onEvent(IOEvent event) {
		switch (event.type) {
		case Data.TIME_CHANGED:
			if (_total.getText() != Data.time) {
				_total.setText(Data.time);
				Dimension d = _total.getMinimumSize();
				_total.setSize(d);
				if (Data.trackingTime > 2000) {
					_total.setLocation((int) ((Data.MAIN_FRAME_WIDTH - d.width) * .5) - 10, 5);
					_resetBox.setLocation(_total.getLocation().x + _total.getSize().width + 2, 14);
					if (_color != Color.WHITE)
						dispatchEvent(Data.RESET_ENABLED);
						_resetBox.setVisible(true);
				} else {
					_total.setLocation((int) ((Data.MAIN_FRAME_WIDTH - d.width) * .5), 5);
					dispatchEvent(Data.RESET_DISABLED);					
					_resetBox.setVisible(false);
				}
			}
		case Data.PERIOD_CHANGED:
			if (_preiod.getText() != Data.period)
				_preiod.setText(Data.period);
			Dimension d = _preiod.getMinimumSize();
			_preiod.setSize(d);
			_preiod.setLocation((int) ((Data.MAIN_FRAME_WIDTH - d.width) * .5), 40);
			break;
		case Data.START_DRAW:
			setVisible(true);
			break;
		case Data.STOP_DRAW:
			break;
		case Data.RESET:
			if (!Data.mouseTrackRecording)
				setVisible(false);
			break;
		case Data.MULTI_MONITOR_USAGE_CHANGED:
			if (!Data.mouseTrackRecording)
				setVisible(false);
			break;
		case Data.COLOR_SCHEME_CHANGED:
			if (!Data.mouseTrackRecording)
				setVisible(false);
			break;
		}
	}

	/**
	 * This method initializes _resetBox
	 * 
	 * @return javax.swing.JCheckBox
	 */
	private JCheckBox get_resetBox() {
		if (_resetBox == null) {
			_resetBox = new JCheckBox();
			_resetBox.setBounds(new Rectangle(0, 0, 29, 23));

			URL url = this.getClass().getResource(Data.RESOURCE_DIRECTORY + "ResetBtn.png");
			_resetBox.setIcon(new ImageIcon(url));
			url = this.getClass().getResource(Data.RESOURCE_DIRECTORY + "ResetPressedBtn.png");
			_resetBox.setPressedIcon(new ImageIcon(url));

			_resetBox.setOpaque(false);
			_resetBox.setToolTipText("Start from scratch");
			if (_color != Color.WHITE)
				_resetBox.setVisible(false);
			_resetBox.addItemListener(new java.awt.event.ItemListener() {
				public void itemStateChanged(java.awt.event.ItemEvent e) {
					if (IOGraph.resetConfirmation()) dispatchEvent(Data.RESET);
				}
			});
		}
		return _resetBox;
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