# Bot-Testing
This is a multi-purpose Discord bot built using Python and the discord.py library. It includes:

1.AI chat using Google Gemini API
2.Advanced reminder system with auto-delete for expired reminders
3.Poll creation and voting
4.AI-powered message summarization
5.Custom welcome messages for new members
6.Music player with queue system
*Features
1.Music Player
!play <URL> - Plays audio from a YouTube link.
!queue - Displays the current queue of songs.
!skip - Skips the current song.
!stop - Stops playback and disconnects the bot.
2.Reminder System
!remind <DD-MM-YYYY> <HH:MM> <message> - Sets a reminder.
!reminders - Lists all active reminders.
!delete_reminder <ID> - Deletes a specific reminder.
!modify_reminder <ID> <new date> <new time> <new message> - Modifies a reminder.
Expired reminders are automatically deleted.
3.Poll System
!poll <question> <option1> <option2> ... - Creates a poll with up to 10 options.
!close_poll <message_id> - Closes a poll and displays results.
4.AI Chat (Google Gemini API)
!chat <message> - Generates AI-powered responses using Google's Gemini API.
5.AI Summarization
!summarize <message> - Summarizes long messages into concise summaries.
6.Welcome Messages
Automatically welcomes new members in the #welcome channel.


*** Features that Worked Well***
AI Chat (!chat)
Reminder System (!remind, !reminders, !delete_reminder, !modify_reminder)
Poll System (!poll, !close_poll)
AI Summarization (!summarize)
***Features That Were Not Properly Tested***
Welcome Messages – The feature was implemented but not fully tested in a live server environment. It may need debugging or adjustments.
Music System – Due to issues with FFmpeg on my device, the music system (!play, !queue, !skip, !stop) was not properly tested. Users may need to troubleshoot FFmpeg installation if they encounter issues.
