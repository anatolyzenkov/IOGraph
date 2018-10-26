package com.iographica.gui;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.image.BufferedImage;
import java.util.ArrayList;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JEditorPane;
import javax.swing.JPanel;
import javax.swing.JTextPane;
import javax.swing.Timer;
import javax.swing.event.HyperlinkEvent;
import javax.swing.event.HyperlinkEvent.EventType;
import javax.swing.event.HyperlinkListener;
import javax.swing.text.Document;
import javax.swing.text.html.HTMLEditorKit;
import javax.swing.text.html.StyleSheet;

import com.iographica.core.Data;
import com.iographica.core.IOGraph;
import com.iographica.core.WebSurfer;
import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;
import com.iographica.utils.MathUtils;

public class NotificationBar extends JPanel implements IEventDispatcher, IEventHandler {
	private static final long serialVersionUID = 1L;
	private BufferedImage _background;
	private JButton _closeBtn;
	private ArrayList<IEventHandler> _eventHandlers;
	private Timer _timer;
	private int _count = 0;
	private int _direction;
	private static final int MAX_COUNT = 20;
	private static final int HEIGHT = 35;

	public NotificationBar() {
		setSize(Data.MAIN_FRAME_WIDTH, HEIGHT);
		setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH, HEIGHT));
		setOpaque(false);
		setLayout(new BorderLayout());
		setBorder(BorderFactory.createEmptyBorder(9, 8, 9, 4));
		setLocation(0, -HEIGHT);
		_background = IOGraph.getBufferedImage("NotificationBar.png");
		String t = "Feel free to <a href=\"" + Data.DONATE_URL + "\">donate</a> for IOGraphica project development.";
		JEditorPane jet = new JEditorPane();
		jet.setEditable(false);
		HTMLEditorKit kit = new HTMLEditorKit();
		jet.setEditorKit(kit);
		StyleSheet style = kit.getStyleSheet();
		style.addRule("body { font-family: " + (new JTextPane()).getFont().getFamily() + ";  font-size: 12pt; color: #d7eef1; }");
		style.addRule("a { color: #FFFFFF; }");
		Document doc = kit.createDefaultDocument();
		jet.setDocument(doc);
		jet.setText("<html><body>" + t + "</body></html>");
		jet.setOpaque(false);
		jet.addHyperlinkListener(new HyperlinkListener() {
			public void hyperlinkUpdate(HyperlinkEvent e) {
				if (e.getEventType() == EventType.ACTIVATED) {
					_closeBtn.setEnabled(false);
					dispatchEvent(Data.CLOSE_NOTIFICATION_BAR);
					WebSurfer.get(e.getURL().toString());
				}
			}
		});
		add(jet, BorderLayout.LINE_START);

		_closeBtn = new JButton(IOGraph.getIcon("NotificationBarCloseBtn.png"));
		_closeBtn.setRolloverEnabled(true);
		_closeBtn.setPressedIcon(IOGraph.getIcon("NotificationBarCloseBtnC.png"));
		_closeBtn.setBorder(BorderFactory.createEmptyBorder());
		_closeBtn.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				_closeBtn.setEnabled(false);
				dispatchEvent(Data.CLOSE_NOTIFICATION_BAR);
			}
		});
		add(_closeBtn, BorderLayout.LINE_END);
		
		_timer = new Timer(20, new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				_count+=_direction;
				_count = Math.min(Math.max(0, _count),MAX_COUNT); 
				switch (_direction) {
				case 1:
					if (_count == MAX_COUNT) _timer.stop();
					break;
				case -1:
					if (_count == 0) _timer.stop();
					break;
				}
				float n = MathUtils.smooth((float)_count/(float)MAX_COUNT, 1);
				setLocation(0, -(int)(HEIGHT*(1f-n)));
			}
		});
	}

	@Override
	protected void paintComponent(Graphics g) {
		super.paintComponent(g);
		if (_count == 0) return;
		g.drawImage(_background, 0, 0, null);
	}

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

	public void onEvent(IOEvent event) {
		switch (event.type) {
		case Data.OPEN_NOTIFICATION_BAR:
			_direction = 1;
			_timer.start();
			break;
		case Data.CLOSE_NOTIFICATION_BAR:
			_direction = -1;
			_timer.start();
			break;
		}

	}
}