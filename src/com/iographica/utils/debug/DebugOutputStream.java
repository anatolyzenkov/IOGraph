package com.iographica.utils.debug;

import java.io.IOException;
import java.io.OutputStream;

import javax.swing.JTextArea;
import javax.swing.SwingUtilities;

public class DebugOutputStream extends OutputStream {
	private final JTextArea _textArea;
	private final StringBuilder _stringBuilder = new StringBuilder();
	private String _title;

	public DebugOutputStream(final JTextArea textArea, String title) {
		this._textArea = textArea;
		this._title = title;
		_stringBuilder.append(title + "> ");
	}

	@Override
	public void flush() {
		System.out.println("flush");
	}

	@Override
	public void close() {
		System.out.println("close");
	}

	@Override
	public void write(int b) throws IOException {
		if (b == '\r') return;
		if (b == '\n') {
			final String text = _stringBuilder.toString() + "\n";
			SwingUtilities.invokeLater(new Runnable() {
				public void run() {
					_textArea.append(text);
				}
			});
			_stringBuilder.setLength(0);
			_stringBuilder.append(_title + "> ");
			return;
		}
		_stringBuilder.append((char) b);
	}
}
