package com.iographica.gui;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Calendar;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JDialog;
import javax.swing.JEditorPane;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextPane;
import javax.swing.SwingConstants;
import javax.swing.event.HyperlinkEvent;
import javax.swing.event.HyperlinkEvent.EventType;
import javax.swing.event.HyperlinkListener;
import javax.swing.text.Document;
import javax.swing.text.html.HTMLEditorKit;
import javax.swing.text.html.StyleSheet;

import com.iographica.core.Data;
import com.iographica.core.IOGraph;
import com.iographica.core.WebSurfer;

public class AboutDialog extends JDialog {
	private static final long serialVersionUID = 1L;

	public AboutDialog(JFrame jFrame) {
		//TODO: Rewrite to awt somehow.
		super(jFrame);
		setSize(new Dimension(418, 290));
		setResizable(false);
		setTitle("About IOGraph");
		setModal(true);
		JPanel jp = new JPanel();
		setContentPane(jp);
		jp.setLayout(new BorderLayout());
		jp.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));

		Calendar cal = Calendar.getInstance();
		String t = Data.APPLICATION_NAME + " V" + Data.getApplicationVersion()
				+ "<br><a href='"+Data.WEBSITE_URL+"'>"+Data.WEBSITE_URL+"</a>"
				+ "<br> <a href='"+Data.ZENKOV_WEBSITE_URL+"'>Anatoly Zenkov</a> & <a href='"+Data.SHIPILOV_WEBSITE_URL+"'>Andrey Shipilov</a>, 2010" + cal.get(Calendar.YEAR) + "."
				+ "<br>"
				+ "<br>IOGraph is a free software supported only by&nbsp;our enthusiasm and your <a href='"+Data.DONATE_URL+"'>donations</a>. "
				+ "<br>Join our <a href='"+Data.FACEBOOK_PAGE_URL+"'>Facebook community</a> to&nbsp;be&nbsp;up to&nbsp;date with IOGraph's timeline."
				+ "<br>"
				+ "<br>This programm is using SimpleAudioPlayer.java by&nbsp;Matthias Pfisterer."
				+ "<br>"
				+ "<br>Inspired by community.";
		JEditorPane jet = new JEditorPane();
		jet.setEditable(false);
		HTMLEditorKit kit = new HTMLEditorKit();
		jet.setEditorKit(kit);
		StyleSheet style = kit.getStyleSheet();
		style.addRule("body { font-family: " + (new JTextPane()).getFont().getFamily() + ";  font-size: 11pt; }");
		Document doc = kit.createDefaultDocument();
		jet.setDocument(doc);
		jet.setText("<html><body>" + t + "</body></html>");
		jet.setOpaque(false);
		jet.addHyperlinkListener(new HyperlinkListener() {
			public void hyperlinkUpdate(HyperlinkEvent e) {
				if (e.getEventType() == EventType.ACTIVATED) {
					WebSurfer.get(e.getURL().toString());
				}
			}
		});
		jp.add(jet, BorderLayout.CENTER);

		FlowLayout flowLayout = new FlowLayout();
		flowLayout.setVgap(0);
		flowLayout.setAlignment(FlowLayout.RIGHT);
		JPanel bjp = new JPanel();
		bjp.setLayout(flowLayout);
		bjp.setBorder(BorderFactory.createEmptyBorder(10, 60, 0, 0));
		JButton cb = new JButton("Close");
		cb.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {
				setVisible(false);
			}
		});
		bjp.add(cb, null);
		jp.add(bjp, BorderLayout.SOUTH);
		
		JLabel jl = new JLabel();
		jl.setIcon(IOGraph.getIcon("DialogIcon.png"));
		jl.setHorizontalAlignment(SwingConstants.LEADING);
		jl.setVerticalAlignment(SwingConstants.TOP);
		jl.setText("");
		bjp = new JPanel();
		bjp.setLayout(new BorderLayout());
		bjp.setPreferredSize(new Dimension(70, 100));
		bjp.add(jl, BorderLayout.CENTER);
		jp.add(bjp, BorderLayout.WEST);
	}

	@Override
	public void setVisible(boolean b) {
		this.setLocation((int) (getOwner().getX() + (getOwner().getWidth() - this.getWidth()) * .5), (int) (getOwner().getY() + (getOwner().getHeight() - this.getHeight()) * .5));
		super.setVisible(b);
	}
}