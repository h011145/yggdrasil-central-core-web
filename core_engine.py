#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CORE ENGINE: Yggdrasil Game System
# DESCRIPTION: Provides the foundational BaseArchive class and core utilities.

import curses

class BaseArchive:
    """
    Abstract base class for all 'Archive' modules (games).
    Ensures a common interface for the Manager Layer to call.
    """
    def __init__(self, stdscr, profile):
        """
        Initializes the archive.

        Args:
            stdscr: The main curses screen object.
            profile (dict): The player's profile data (e.g., points, upgrades).
        """
        self.stdscr = stdscr
        self.profile = profile
        self.is_running = True
        self.logs = [] # Initialize logs attribute here

    def safe_addstr(self, y, x, text, style=0):
        """
        A safe wrapper for curses addstr that prevents out-of-bounds errors.
        """
        h, w = self.stdscr.getmaxyx()
        if y >= h or x >= w or y < 0 or x < 0:
            return
        
        # Truncate text if it exceeds screen width
        safe_text = text
        if len(text) >= w - x:
            safe_text = text[:w - x - 1]

        try:
            self.stdscr.addstr(y, x, safe_text, style)
        except curses.error:
            pass

    def refresh_logs(self):
        """
        Refreshes the log display area.
        Assumes log area starts at h - 6 from the bottom.
        """
        h, w = self.stdscr.getmaxyx()
        log_start_y = h - 6 # Example start line for logs, can be adjusted
        
        # Clear log area
        for i in range(5): # Max 5 lines of logs
            self.stdscr.move(log_start_y + i, 0)
            self.stdscr.clrtoeol()

        # Redraw logs
        for i, m in enumerate(self.logs[-5:]):
            self.safe_addstr(log_start_y + i, 2, f"> {m}") # x=2 for indentation
        self.stdscr.refresh()

    def play(self):
        """
        The main entry point for the archive's gameplay loop.
        This method must be implemented by all child classes.
        It should return a dictionary report of the results.
        """
        raise NotImplementedError("The 'play' method must be implemented in the child archive class.")