package com.iographica.gui;

import java.awt.Dimension;

import javax.swing.JPanel;

import com.iographica.core.Data;


public class FrontPanel extends JPanel {

	private static final long serialVersionUID = 1L;

	/**
	 * This is the default constructor
	 */
	public FrontPanel() {
		super();
		initialize();
	}

	/**
	 * This method initializes this
	 * 
	 * @return void
	 */
	private void initialize() {
		this.setLayout(null);
		this.setSize(Data.MAIN_FRAME_WIDTH, Data.PANEL_HEIGHT);
		this.setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH, Data.PANEL_HEIGHT));
	}

}
