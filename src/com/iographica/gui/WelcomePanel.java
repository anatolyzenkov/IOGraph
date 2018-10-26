package com.iographica.gui;

import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.Font;

import javax.swing.BorderFactory;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.SwingConstants;

import com.iographica.core.Data;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;

public class WelcomePanel extends JPanel implements IEventHandler {

	private static final long serialVersionUID = 1L;
	private JLabel _preiod = null;
	private Color _color;

	/**
	 * This is the default constructor
	 */
	public WelcomePanel(Color color) {
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
		_preiod.setText("Press button above to start mouse tracking.");
		_preiod.setOpaque(false);
		_preiod.setHorizontalAlignment(SwingConstants.CENTER);
		_preiod.setHorizontalTextPosition(SwingConstants.CENTER);
		_preiod.setVerticalAlignment(SwingConstants.CENTER);
		_preiod.setVerticalTextPosition(SwingConstants.CENTER);
		_preiod.setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH, Data.PANEL_HEIGHT));
		_preiod.setForeground(_color);

		this.setSize(465, 66);
		this.setSize(Data.MAIN_FRAME_WIDTH, Data.PANEL_HEIGHT);
		this.setLayout(new BorderLayout());
		this.setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH, Data.PANEL_HEIGHT));
		this.setBorder(BorderFactory.createEmptyBorder(0, 0, 3, 0));
		this.add(_preiod, BorderLayout.WEST);
	}

	public void onEvent(IOEvent event) {
		switch (event.type) {
		case Data.START_DRAW:
			setVisible(false);
			break;
		case Data.RESET:
			if (!Data.mouseTrackRecording) setVisible(true);
			break;
		case Data.MULTI_MONITOR_USAGE_CHANGED:
			if (!Data.mouseTrackRecording) setVisible(true);
			break;
		case Data.COLOR_SCHEME_CHANGED:
			if (!Data.mouseTrackRecording) setVisible(true);
			break;
		}
	}
}