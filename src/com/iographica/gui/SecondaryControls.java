package com.iographica.gui;

import java.awt.Color;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.util.ArrayList;

import javax.swing.BorderFactory;
import javax.swing.JCheckBox;
import javax.swing.JPanel;
import javax.swing.Timer;

import com.iographica.core.Data;
import com.iographica.core.IOGraph;
import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;
import com.iographica.events.IOEvent;


public class SecondaryControls extends JPanel implements IEventDispatcher, IEventHandler {
	private static final String SAVE_BTN = "SaveBtn";
	private static final String SAVE_PRESSED_BTN = "SavePressedBtn";
	private static final String SAVE_DISABLED_BTN = "SaveDisabledBtn";
	private static final String EXTENSION = ".png";
	private static final long serialVersionUID = 1L;
	private JCheckBox _saveBtn = null;
	private JCheckBox _setupBtn = null;
	private JCheckBox _urlBtn = null;
	private ArrayList<IEventHandler> _eventHandlers;
	private Timer _timer;
	private String _saveIconJoke;

	/**
	 * This is the default constructor
	 */
	public SecondaryControls() {
		super();
		_timer = new Timer(10000, new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				_setupBtn.setSelected(false);
				_timer.stop();
			}
		});

		initialize();
	}

	/**
	 * This method initializes this
	 * 
	 * @return void
	 */
	private void initialize() {
		FlowLayout flowLayout = new FlowLayout();
		flowLayout.setHgap(0);
		flowLayout.setVgap(0);
		this.setLayout(flowLayout);
		this.setSize(30, Data.PANEL_HEIGHT);
		this.setBorder(BorderFactory.createEmptyBorder(5, 0, 10, 0));
		this.setBackground(Color.GRAY);
		this.add(get_saveBtn(), null);
		this.add(get_setupBtn(), null);
		this.add(get_urlBtn(), null);
	}

	/**
	 * This method initializes _saveBtn
	 * 
	 * @return javax.swing.JCheckBox
	 */
	private JCheckBox get_saveBtn() {
		if (_saveBtn == null) {
			_saveBtn = new JCheckBox();
			_saveIconJoke = "";
			if (System.getProperty("os.name").indexOf("Windows") != -1) {
				//_saveIconJoke = "Win";
			}
			_saveBtn.setIcon(IOGraph.getIcon(SAVE_BTN+_saveIconJoke+EXTENSION));
			_saveBtn.setToolTipText("Save image");
			_saveBtn.setPressedIcon(IOGraph.getIcon(SAVE_PRESSED_BTN+_saveIconJoke+EXTENSION));
			_saveBtn.setEnabled(false);
			_saveBtn.setDisabledIcon(IOGraph.getIcon(SAVE_DISABLED_BTN+_saveIconJoke+EXTENSION));
			_saveBtn.addItemListener(new java.awt.event.ItemListener() {
				public void itemStateChanged(java.awt.event.ItemEvent e) {
					String c = "";//"C";
					if (e.getStateChange() == ItemEvent.SELECTED) {
						dispatchEvent(Data.SAVE_IMAGE);
					} else {
						c = "";
						_saveBtn.setEnabled(true);
					}
					_saveBtn.setIcon(IOGraph.getIcon(SAVE_BTN+_saveIconJoke+c+EXTENSION));
					_saveBtn.setPressedIcon(IOGraph.getIcon(SAVE_PRESSED_BTN+_saveIconJoke+c+EXTENSION));
				}
			});
			setupBtn(_saveBtn);
		}
		return _saveBtn;
	}

	private void setupBtn(JCheckBox btn) {
		btn.setSize(19, 18);
		btn.setPreferredSize(new Dimension(19, 18));
		btn.setOpaque(false);
	}

	/**
	 * This method initializes _setupBtn
	 * 
	 * @return javax.swing.JCheckBox
	 */
	private JCheckBox get_setupBtn() {
		if (_setupBtn == null) {
			_setupBtn = new JCheckBox();
			_setupBtn.setIcon(IOGraph.getIcon("SetupBtn.png"));
			_setupBtn.setToolTipText("Show control panel");
			_setupBtn.setPressedIcon(IOGraph.getIcon("SetupPressedBtn.png"));
			_setupBtn.addItemListener(new java.awt.event.ItemListener() {
				public void itemStateChanged(java.awt.event.ItemEvent e) {
					if (e.getStateChange() == ItemEvent.SELECTED) {
						_setupBtn.setIcon(IOGraph.getIcon("SetupBtnC.png"));
						_setupBtn.setPressedIcon(IOGraph.getIcon("SetupPressedBtnC.png"));
						_setupBtn.setToolTipText("Hide control panel");
						dispatchEvent(Data.OPEN_CONTROLS);
					} else {
						_setupBtn.setIcon(IOGraph.getIcon("SetupBtn.png"));
						_setupBtn.setPressedIcon(IOGraph.getIcon("SetupPressedBtn.png"));
						_setupBtn.setToolTipText("Show control panel");
						dispatchEvent(Data.CLOSE_CONTROLS);
					}
				}
			});
			setupBtn(_setupBtn);
		}
		return _setupBtn;
	}

	/**
	 * This method initializes _urlBtn
	 * 
	 * @return javax.swing.JCheckBox
	 */
	private JCheckBox get_urlBtn() {
		if (_urlBtn == null) {
			_urlBtn = new JCheckBox();
			_urlBtn.setIcon(IOGraph.getIcon("URLBtn.png"));
			_urlBtn.setToolTipText("Visit IOGraphica website");
			_urlBtn.setPressedIcon(IOGraph.getIcon("URLPressedBtn.png"));
			_urlBtn.addItemListener(new java.awt.event.ItemListener() {
				public void itemStateChanged(java.awt.event.ItemEvent e) {
					if (e.getStateChange() == ItemEvent.SELECTED) {
						_urlBtn.setIcon(IOGraph.getIcon("URLBtnC.png"));
						_urlBtn.setPressedIcon(IOGraph.getIcon("URLPressedBtnC.png"));
						dispatchEvent(Data.GET_URL);
						_urlBtn.setSelected(false);
					} else {
						_urlBtn.setIcon(IOGraph.getIcon("URLBtn.png"));
						_urlBtn.setPressedIcon(IOGraph.getIcon("URLPressedBtn.png"));
					}
				}
			});
			setupBtn(_urlBtn);
		}
		return _urlBtn;
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
		case Data.IMAGE_SAVED:
			_saveBtn.setSelected(false);
			break;
		case Data.CLOSE_CONTROLS:
			_setupBtn.setSelected(false);
			break;
		case Data.RESET:
			if (!Data.mouseTrackRecording)
				_saveBtn.setEnabled(false);
			break;
		case Data.START_DRAW:
			_saveBtn.setEnabled(true);
			break;
		default:
			break;
		}
	}

	public void focusLost() {
		if (!Data.preventControlsHiding) _timer.start();
	}

	public void focusGained() {
		_timer.stop();
	}

} // @jve:decl-index=0:visual-constraint="10,10"
