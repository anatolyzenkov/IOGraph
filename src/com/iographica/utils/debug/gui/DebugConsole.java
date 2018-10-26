package com.iographica.utils.debug.gui;

import java.awt.Rectangle;
import java.io.PrintStream;

import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

import com.iographica.utils.debug.DebugOutputStream;

public class DebugConsole extends JFrame {
	private static final long serialVersionUID = -1863821816064278837L;
	private DebugOutputStream taOutputStream;

	public DebugConsole() {
		// this.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		this.setBounds(new Rectangle(0, 22, 465, 800));
		this.setResizable(false);
		this.setTitle("Console");
		JPanel mainPanel = new JPanel();
		this.setContentPane(mainPanel);

		// Create Frame
		JTextArea ta = new JTextArea("", 20, 50);
		ta.setLineWrap(true);
		JScrollPane sbrText = new JScrollPane(ta);
		sbrText.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);
		mainPanel.add(sbrText);
		taOutputStream = new DebugOutputStream(ta, "");
		System.setOut(new PrintStream(taOutputStream));
		pack();
		setVisible(true);
	}
}
