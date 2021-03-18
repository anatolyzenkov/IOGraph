package com.iographica.gui;

import java.awt.AWTException;
import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.Image;
import java.awt.MenuItem;
import java.awt.PopupMenu;
import java.awt.Rectangle;
import java.awt.SystemTray;
import java.awt.Toolkit;
import java.awt.TrayIcon;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;

import javax.swing.BoxLayout;
import javax.swing.JFrame;
import javax.swing.JLayeredPane;
import javax.swing.JPanel;
import javax.swing.WindowConstants;

import com.iographica.core.Data;
import com.iographica.core.IOGraph;
import com.iographica.events.IEventDispatcher;
import com.iographica.events.IEventHandler;

public class MainFrame extends JFrame implements IEventDispatcher {

	private static final long serialVersionUID = 1L;
	private JPanel _mainPanel = null;
	private JLayeredPane _outputPanel = null;
	private JPanel _bottomPanel = null;
	private ArrayList<IEventHandler> _eventHandlers;

	/**
	 * This is the default constructor
	 */
	public MainFrame() {
		super();
		initialize();
		ArrayList<Image> imageList = new ArrayList<Image>();
		imageList.add(IOGraph.getIcon("icon16.png").getImage());
		imageList.add(IOGraph.getIcon("icon32.png").getImage());
		imageList.add(IOGraph.getIcon("icon64.png").getImage());
		imageList.add(IOGraph.getIcon("icon128.png").getImage());
		imageList.add(IOGraph.getIcon("icon256.png").getImage());
		imageList.add(IOGraph.getIcon("icon512.png").getImage());
		setIconImages(imageList);
		//Why these images so "dry" when frame minimized?
		
        TrayIcon trayIcon = null;
        if (SystemTray.isSupported()) {
            // get the SystemTray instance
            SystemTray tray = SystemTray.getSystemTray();
            // load an image
            Image image;
			try {
				image = Toolkit.getDefaultToolkit().getImage(new URL("http://cdn1.iconfinder.com/data/icons/Hypic_Icon_Pack_by_shlyapnikova/16/forum_16.png"));
				// create a action listener to listen for default action executed on the tray icon
	            ActionListener listener = new ActionListener() {
	                public void actionPerformed(ActionEvent e) {
	                    System.out.println("action");
	                    // execute default action of the application
	                    // ...
	                }
	            };
	            // create a popup menu
	            PopupMenu popup = new PopupMenu();
	            // create menu item for the default action
	            MenuItem defaultItem = new MenuItem("Do the action");
	            defaultItem.addActionListener(listener);
	            popup.add(defaultItem);
	            /// ... add other items
	            // construct a TrayIcon
	            trayIcon = new TrayIcon(image, "Tray Demo", popup);
	            // set the TrayIcon properties
	            trayIcon.addActionListener(listener);
	            // ...
	            // add the tray image
			} catch (MalformedURLException e1) {
				// TODO Auto-generated catch block
				e1.printStackTrace();
			}
            
            try {
                tray.add(trayIcon);
            } catch (AWTException e) {
                System.err.println(e);
            }
            // ...
        } else {
            // disable tray option in your application or
            // perform other actions
            //...
        }
        // ...
        // some time later
        // the application state has changed - update the image
        if (trayIcon != null) {
            //trayIcon.setImage(updatedImage);
        }

	}

	/**
	 * This method initializes this
	 * 
	 * @return void
	 */
	private void initialize() {
		this.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
		this.setBounds(new Rectangle(0, 22, 465, 400));
		this.setResizable(false);
		this.setTitle(Data.APPLICATION_NAME);
		this.setSize(Data.MAIN_FRAME_WIDTH, 400);
		this.setContentPane(get_mainPanel());
		this.setBackground(Data.BACKGROUND_COLOR);
		this.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);
		this.addWindowListener(new java.awt.event.WindowAdapter() {
			public void windowDeactivated(java.awt.event.WindowEvent e) {
				_bottomPanel.setBackground(Data.OUT_OF_FOCUS_BACKGROUND_COLOR);
			}

			public void windowActivated(java.awt.event.WindowEvent e) {
				_bottomPanel.setBackground(Data.BACKGROUND_COLOR);
			}
		});
	}

	/**
	 * This method initializes _mainPanel
	 * 
	 * @return javax.swing.JPanel
	 */
	private JPanel get_mainPanel() {
		if (_mainPanel == null) {
			_mainPanel = new JPanel();
			_mainPanel.setLayout(new BoxLayout(get_mainPanel(), BoxLayout.Y_AXIS));
			_mainPanel.add(get_outputPanel(), BorderLayout.CENTER);
			_mainPanel.add(get_bottomPanel(), null);
		}
		return _mainPanel;
	}

	public JLayeredPane get_outputPanel() {
		if (_outputPanel == null) {
			_outputPanel = new JLayeredPane();
			_outputPanel.setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH, 100));
			_outputPanel.setOpaque(false);
		}
		return _outputPanel;
	}

	public JPanel get_bottomPanel() {
		if (_bottomPanel == null) {
			_bottomPanel = new JPanel();
			_bottomPanel.setLayout(null);
			_bottomPanel.setPreferredSize(new Dimension(Data.MAIN_FRAME_WIDTH, Data.PANEL_HEIGHT));
		}
		return _bottomPanel;
	}

	public void addEventHandler(IEventHandler handler) {
		if (_eventHandlers == null) {
			_eventHandlers = new ArrayList<IEventHandler>();
		}
		_eventHandlers.add(handler);
	}
}