package com.iographica.core;

import java.awt.Component;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.Timer;

import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;
import com.iographica.utils.MathUtils;


public class PanelSwaper implements IEventHandler {
	private int _count = 0;
	private Timer _timer;
	private int _direction;
	private Component _c0;
	private Component _c1;
	private static final int _maxCount = 30;

	public PanelSwaper(Component c0, Component c1) {
		_count = 0;
		_c0 = c0;
		_c1 = c1;
		_timer = new Timer(20, new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				_count+=_direction;
				_count = Math.min(Math.max(0, _count),_maxCount); 
				switch (_direction) {
				case 1:
					if (_count == _maxCount) _timer.stop();
					break;
				case -1:
					if (_count == 0) _timer.stop();
					break;
				}
				float n = MathUtils.smooth((float)_count/(float)_maxCount, 1);
				_c0.setLocation(0, -(int)(Data.PANEL_HEIGHT*n));
				_c1.setLocation(0, (int)(Data.PANEL_HEIGHT*(1f-n)));
			}
		});
	}

	public void onEvent(IOEvent event) {
		switch (event.type) {
		case Data.OPEN_CONTROLS:
			_direction = 1;
			_timer.start();
			break;
		case Data.CLOSE_CONTROLS:
			_direction = -1;
			_timer.start();
			break;
		}
	}
}
