package com.iographica.core;

import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.Calendar;

import javax.swing.Timer;

import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;

public class TrackingTimer implements IEventDispatcher, IEventHandler {

	private ArrayList<IEventHandler> _eventHandlers;
	private Calendar _startCal;
	private Calendar _endCal;
	private Timer _timer;
	private final String[] M_NAMES = new String[12];
	private final int DELAY = 1000;
	private final int MINUTE = 60 * 1000;
	private final float FSECOND = 1000;
	private final float FMINUTE = 60 * 1000;
	private final float FHOUR = 60 * 60 * 1000;
	private final float FDAY = 24 * 60 * 60 * 1000;
	private boolean _fullDateTreatment;

	public TrackingTimer() {
		Data.trackingTime = 0;
		_fullDateTreatment = false;
		_timer = new Timer(DELAY, new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				Data.trackingTime += DELAY;
				treatTime();
				treatPeriod();
			}
		});
		M_NAMES[0] = "Jan";
		M_NAMES[1] = "Feb";
		M_NAMES[2] = "Mar";
		M_NAMES[3] = "Apr";
		M_NAMES[4] = "May";
		M_NAMES[5] = "Jun";
		M_NAMES[6] = "Jul";
		M_NAMES[7] = "Aug";
		M_NAMES[8] = "Sep";
		M_NAMES[9] = "Oct";
		M_NAMES[10] = "Nov";
		M_NAMES[11] = "Dec";
	}

	protected void treatTime() {
		float n;
		float t = Data.trackingTime;
		if (t / FSECOND < 1f) {
			Data.time = "Just started";
		} else if (t / FMINUTE < 1f) {
			n = t / FSECOND;
			Data.time = ((int) n) + (n == 1 ? " second" : " seconds");
		} else if (t / FHOUR < 1f) {
			n = t / FMINUTE;
			Data.time = ((int) n) + (n == 1 ? " minute" : " minutes");
		} else if (t / FDAY < 1f) {
			n = t / FHOUR;
			Data.time = presision(n) + (n < 1.1 ? " hour" : " hours");
		} else {
			n = t / FDAY;
			Data.time = presision(n) + (n < 1.1 ? " day" : " days");
		}
		dispatchEvent(Data.TIME_CHANGED);
	}

	private void treatPeriod() {
		_endCal = Calendar.getInstance();
		boolean endDataTreatment = _endCal.getTimeInMillis() - _startCal.getTimeInMillis() > MINUTE;
		Data.usePeriod = endDataTreatment;
		_fullDateTreatment = (_startCal.get(Calendar.DATE) != _endCal.get(Calendar.DATE) || _startCal.get(Calendar.MONTH) != _endCal.get(Calendar.MONTH)) && endDataTreatment;
		String s = "From " + datePattern(_startCal);
		if (endDataTreatment) {
			s += " to " + datePattern(_endCal);
		}
		Data.period = s;
		dispatchEvent(Data.PERIOD_CHANGED);
	}

	private String datePattern(Calendar cal) {
		String min = "0" + cal.get(Calendar.MINUTE);
		String s = cal.get(Calendar.HOUR_OF_DAY) + ":" + min.substring(min.length() - 2, min.length());
		if (_fullDateTreatment) {
			s += " " + M_NAMES[cal.get(Calendar.MONTH)] + " " + convertDate(cal.get(Calendar.DATE));
		}
		return s;
	}

	private String convertDate(int date) {
		String s = date + "";
		switch (date) {
		case 1:
			s += "st";
			break;
		case 2:
			s += "nd";
			break;
		case 3:
			s += "rd";
			break;
		default:
			s += "th";
			break;
		}
		return s;
	}

	private String presision(float n) {
		String s = (n + "");
		if (n%1f < .1f) return (((int) n) + "");
		return s.substring(0, s.indexOf(".") + 2);
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

	public void onEvent(IOEvent event) {
		switch (event.type) {
		case Data.START_DRAW:
			if (_startCal == null) {
				_startCal = Calendar.getInstance();
			}
			_timer.start();
			treatTime();
			treatPeriod();
			break;
		case Data.STOP_DRAW:
			_timer.stop();
			break;
		case Data.RESET:
			reset();
			break;
		case Data.COLOR_SCHEME_CHANGED:
			reset();
			break;
		case Data.MULTI_MONITOR_USAGE_CHANGED:
			reset();
			break;
		}
	}

	private void reset() {
		Data.trackingTime = 0;
		_endCal = null;
		if (Data.mouseTrackRecording) {
			_startCal = Calendar.getInstance();
			_timer.restart();
			treatTime();
			treatPeriod();
		} else {
			_startCal = null;
		}
	}
}