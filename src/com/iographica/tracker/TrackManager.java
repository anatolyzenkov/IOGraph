package com.iographica.tracker;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Rectangle;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.MouseEvent;
import java.awt.event.MouseListener;
import java.awt.image.BufferedImage;
import java.awt.image.RescaleOp;
import java.io.File;
import java.util.ArrayList;

import javax.swing.ImageIcon;
import javax.swing.JPanel;
import javax.swing.Timer;

import com.iographica.core.Data;
import com.iographica.core.ExportManager;
import com.iographica.core.IOGraph;
import com.iographica.core.SnapshotManager;
import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;

public class TrackManager extends JPanel implements IEventDispatcher, IEventHandler, MouseListener {
	private static final long serialVersionUID = 987747765291380421L;
	private static final int PLAY_BTN_RADIUS = 40;
	private static final int PLAY_BTN_ID = 0;
	private float _scale;
	private BufferedImage _recordBtnPauseImage;
	private BufferedImage _recordBtnRecordImage;
	private int _buttonAlpha;
	private boolean _hitTest;
	private ArrayList<IEventHandler> _eventHandlers;
	private Drawer _drawer;
	private ImageIcon _backgroundPreview;
	private ExportManager _imageExporter;
	private int _playBtnX;
	private int _playBtnY;
	private int _pressTargetId;
	private int _releaseTargetId;
	private Timer _timer;
	private int _mouseX;
	private int _mouseY;

	public TrackManager() {
		addMouseListener(this);
		_recordBtnPauseImage = IOGraph.getBufferedImage("PauseBtn.png");
		_recordBtnRecordImage = IOGraph.getBufferedImage("RecordBtn.png");
		_buttonAlpha = 255;
		_drawer = new Drawer();
		_imageExporter = new ExportManager();
		_imageExporter.addEventHandler(this);
		_timer = new Timer(33, new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				repaint();
			}
		});
		setup();
	}

	public void setup() {
		out("TrackManager.setup()");
		if (Data.useScreenshot) {
			if (!(new File(Data.BACKGROUND_PREVIEW_FILE_NAME)).exists()) return;
		}

		Rectangle rect = SnapshotManager.getScreenBounds(SnapshotManager.FULL_SIZE);

		_scale = (float) Data.MAIN_FRAME_WIDTH / (float) rect.width;
		int pHeight = (int) (rect.height * _scale);
		_playBtnX = (int) ((Data.MAIN_FRAME_WIDTH - getButton().getWidth()) * .5);
		_playBtnY = (int) ((pHeight - getButton().getHeight()) * .5);

		// SETUP OVERLAY IMAGEs
		_drawer.setupImages(rect, _scale);

		// SETUP MAIN CANVAS
		setSize(Data.MAIN_FRAME_WIDTH, pHeight);
		setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH, pHeight));
		if (getParent() != null) {
			getParent().setPreferredSize(getPreferredSize());
			getParent().invalidate();
		}

		// SETUP BACKGROUND IMAGEs
		updateBackground();
		fullUpdate();
	}

	private void updateBackground() {
		if (!Data.useScreenshot) return;
		ImageIcon img = new ImageIcon(Data.BACKGROUND_PREVIEW_FILE_NAME);
		if (img != null) {
			if (_backgroundPreview != null) {
				_backgroundPreview.getImage().flush();
				_backgroundPreview = null;
				System.gc();
			}
			_backgroundPreview = img;
		}
	}

	private void fullUpdate() {
		out("TrackManager.fullUpdate()");
		clear();
		repaint();
	}
	
	@Override
	public void repaint() {
		super.repaint();
		if (Data.mouseTrackRecording) _drawer.update();
	}

	@Override
	public void paintComponent(Graphics g) {
		out("TrackManager.paintComponent()");
		super.paintComponent(g);
		if (Data.useScreenshot && _backgroundPreview != null) {
			g.drawImage(_backgroundPreview.getImage(), 0, 0, null);
		} else {
			clear();
		}

		g.drawImage(_drawer.getPreview(), 0, 0, null);
		
		if (_hitTest || !Data.mouseTrackRecording) {
			if (_buttonAlpha < 255) {
				_buttonAlpha += 30;
				_buttonAlpha = Math.max(0, Math.min(255, _buttonAlpha));
			}
		} else {
			if (_buttonAlpha > 0) {
				_buttonAlpha -= 30;
				_buttonAlpha = Math.max(0, Math.min(255, _buttonAlpha));
			}
		}
		if (_buttonAlpha > 0) {
			float[] scales = { 1f, 1f, 1f, (float) _buttonAlpha / (float) 255 };
			float[] offsets = new float[4];
			RescaleOp rop = new RescaleOp(scales, offsets, null);
			((Graphics2D) g).drawImage(getButton(), rop, _playBtnX, _playBtnY);
			if (_buttonAlpha == 255) if (!Data.mouseTrackRecording) noLoop();
		} else {
			if (!Data.mouseTrackRecording) noLoop();
		}

		g.setColor(new Color(137, 137, 137));
		g.fillRect(0, getHeight() - 2, Data.MAIN_FRAME_WIDTH, 1);
		g.setColor(new Color(235, 235, 235));
		g.fillRect(0, getHeight() - 1, Data.MAIN_FRAME_WIDTH, 1);
	}

	private void clear() {
		if (Data.prefs.getBoolean(Data.USE_COLOR_SCHEME, false)) {
			setBackground(Color.BLACK);
		} else {
			setBackground(Color.WHITE);
		}
	}

	protected void processMouseEvent(MouseEvent e) {
		out("TrackManager.processMouseEvent()");
		_mouseX = e.getX();
		_mouseY = e.getY();
		switch (e.getID()) {
		case MouseEvent.MOUSE_ENTERED:
			_hitTest = true;
			loop();
			break;
		case MouseEvent.MOUSE_EXITED:
			_hitTest = false;
			loop();
			break;
		case MouseEvent.MOUSE_PRESSED:
			getMousePressTarget();
			break;
		case MouseEvent.MOUSE_RELEASED:
			if (_pressTargetId != -1) {
				getMouseReleaseTarget();
				if (_pressTargetId == _releaseTargetId) {
					if (_pressTargetId == PLAY_BTN_ID) play();
				}
				_releaseTargetId = _pressTargetId = -1;
			}
			break;
		}
		super.processMouseEvent(e);
	}

	private void loop() {
		out("TrackManager.loop()");
		_timer.start();
	}

	private void noLoop() {
		out("TrackManager.noLoop()");
		_timer.stop();
	}

	private void getMousePressTarget() {
		out("TrackManager.getMousePressTarget()");
		_pressTargetId = -1;
		if (hitTest(_playBtnX + (int) (_recordBtnRecordImage.getWidth() * .5), _playBtnY + (int) (_recordBtnRecordImage.getHeight() * .5), PLAY_BTN_RADIUS)) {
			_pressTargetId = PLAY_BTN_ID;
			return;
		}
	}

	private void getMouseReleaseTarget() {
		out("TrackManager.getMouseReleaseTarget()");
		_releaseTargetId = -1;
		if (hitTest(_playBtnX + (int) (_recordBtnRecordImage.getWidth() * .5), _playBtnY + (int) (_recordBtnRecordImage.getHeight() * .5), PLAY_BTN_RADIUS)) {
			_releaseTargetId = PLAY_BTN_ID;
			return;
		}
	}

	private Boolean hitTest(int x, int y, int r) {
		out("TrackManager.hitTest()");
		int dx = x - _mouseX;
		int dy = y - _mouseY;
		return dx * dx + dy * dy < r * r;
	}

	private void play() {
		out("TrackManager.play()");
		Data.mouseTrackRecording = !Data.mouseTrackRecording;
		if (Data.mouseTrackRecording) {
			dispatchEvent(Data.START_DRAW);
		} else {
			dispatchEvent(Data.STOP_DRAW);
		}
		repaint();
	}

	private BufferedImage getButton() {
		return Data.mouseTrackRecording ? _recordBtnPauseImage : _recordBtnRecordImage;
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
		out("TrackManager.onEvent()");
		switch (event.type) {
		case Data.UPDATE_BACKGROUND:
			out("UPDATE_BACKGROUND");
			//setup();
			updateBackground();
			repaint();
			break;
		case Data.MULTI_MONITOR_USAGE_CHANGED:
			out("MULTI_MONITOR_USAGE_CHANGED");
			setup();
			break;
		case Data.BACKGROUND_USAGE_CHANGED:
			out("BACKGROUND_USAGE_CHANGED");
			fullUpdate();
			break;
		case Data.SAVE_IMAGE:
			out("SAVE_IMAGE");
			_imageExporter.export(_drawer.getImage());
			break;
		case Data.IMAGE_SAVED:
			out("IMAGE_SAVED");
			if (event.target != this) dispatchEvent(Data.IMAGE_SAVED);
			break;
		case Data.START_DRAW:
			_drawer.prepareForUpdate();
			loop();
			break;
		case Data.STOP_DRAW:
			_buttonAlpha = 255;
			repaint();
			noLoop();
			break;
		case Data.RESET:
			out("RESET");
			_drawer.resetImages();
			fullUpdate();
			break;
		case Data.COLOR_SCHEME_CHANGED:
			out("COLOR_SCHEME_CHANGED");
			_drawer.resetImages();
			fullUpdate();
			break;
		default:
			break;
		}
	}

	private void out(Object object) {
		// System.out.println(object);
	}

	public void mouseClicked(MouseEvent e) {

	}

	public void mouseEntered(MouseEvent e) {

	}

	public void mouseExited(MouseEvent e) {

	}

	public void mousePressed(MouseEvent e) {

	}

	public void mouseReleased(MouseEvent e) {
	}

	public void debugExit() {
		noLoop();
		dispatchEvent(Data.STOP_DRAW);
	}
}