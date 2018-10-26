package com.iographica.osx;

import java.util.ArrayList;

import com.apple.eawt.AppEvent.QuitEvent;
import com.apple.eawt.QuitHandler;
import com.apple.eawt.QuitResponse;
import com.iographica.core.Data;
import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;

public class OSXQuitHandler implements IEventDispatcher, QuitHandler {
	private ArrayList<IEventHandler> _eventHandlers;

	public void handleQuitRequestWith(QuitEvent a, QuitResponse r) {
		dispatchEvent(Data.SYSTEM_QUIT_REQUESTED);
		r.cancelQuit();
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
