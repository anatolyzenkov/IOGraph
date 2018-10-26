package com.iographica.events;

public class IOEvent {
	public int type;
	public Object target;

	public IOEvent(int type, Object target) {
		this.type = type;
		this.target = target;
	}
}