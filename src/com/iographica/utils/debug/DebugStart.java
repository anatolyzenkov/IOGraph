package com.iographica.utils.debug;

import java.awt.Container;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

import javax.swing.BoxLayout;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;

import com.iographica.core.IOGraph;

public class DebugStart extends JFrame implements ActionListener {
	private static final long serialVersionUID = 1L;
	public static void main(String args[]) {
		try {
			UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
		} catch (ClassNotFoundException e) {
			e.printStackTrace();
		} catch (InstantiationException e) {
			e.printStackTrace();
		} catch (IllegalAccessException e) {
			e.printStackTrace();
		} catch (UnsupportedLookAndFeelException e) {
			e.printStackTrace();
		}
		new DebugStart();
	}
	private JPanel _mainPanel;
	private IOGraph _iograph;
	public DebugStart() {
		this.addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent we) {
				System.exit(0);
			}
		});
		this.setContentPane(get_mainPanel());
		pack();
		setVisible(true);
		_iograph = new IOGraph();
	}
	private Container get_mainPanel() {
		if (_mainPanel == null) {
			_mainPanel = new JPanel();
			_mainPanel.setLayout(new BoxLayout(get_mainPanel(), FlowLayout.CENTER));
			_mainPanel.setPreferredSize(new Dimension(200, 50));
			JButton b = new JButton("Restart");
			_mainPanel.add(b);
			b.addActionListener(this);
		}
		return _mainPanel;
	}
	public void actionPerformed(ActionEvent e) {
		if (_iograph != null) {
			_iograph.debugExit();
			_iograph = null;
		}
		_iograph = new IOGraph();
	}
}
