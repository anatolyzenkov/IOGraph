package com.iographica.core;

import java.awt.Desktop;
import java.net.URI;

public class WebSurfer {
	public static void get (String url) {
		try {
			URI uri = new URI(url);
			Desktop desktop = java.awt.Desktop.getDesktop();
			desktop.browse(uri);
		} catch (Exception err) {
			System.err.println(err.getMessage());
		}
	}
}
