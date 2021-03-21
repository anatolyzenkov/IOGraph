package com.iographica.utils.debug.gui;

import java.awt.AlphaComposite;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Rectangle;
import java.util.Date;

import javax.swing.JFrame;
import javax.swing.JPanel;

import com.iographica.core.Data;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;

public class GraphicProfiler extends JPanel  implements IEventHandler{
	private static final long serialVersionUID = -1863821816064278837L;
	private long t = 0;

	public GraphicProfiler() {
		// this.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		JFrame frame = new JFrame();
		frame.setBounds(new Rectangle(0, 22 + 400, 465, 800));
		frame.setResizable(false);
		frame.setTitle("Profiler");
//		this.setSize(600, 400);
		Date date = new Date();
		t = date.getTime();
		
		// Create Frame
		this.setOpaque(true);
		this.setSize(600, 400);
		setPreferredSize(new Dimension(600, 400));
		frame.setResizable(false);
		frame.setContentPane(this);
		frame.pack();
		frame.setVisible(true);
	}
	public void onEvent(IOEvent event) {
		if (event.type == Data.TIME) {			
			Date date = new Date();
			int i = (int)((date.getTime() - t)/20);
			int w = 600;
			int h = 400;
			repaint(new Rectangle(i % w, (int)((i / w) * 4) % h, 1, 4));
		}
	}
	@Override
	public void paintComponent(Graphics g) {
//		out("TrackManager.paintComponent()");
		super.paintComponent(g);
		Rectangle r = g.getClipBounds();
		AlphaComposite ac = AlphaComposite.getInstance(AlphaComposite.SRC_OVER,0.2f);
		((Graphics2D) g).setComposite(ac);
		g.drawRect(r.x, r.y, r.width, r.height);
	}
}
