
# How does this bot work?

in the code, change the values for `APPROVER_ROLE_NAME`, `approval_channel_id` and `final_channel_id`.
```
APPROVER_ROLE_NAME = "record perms" # Submission role name for perms
approval_channel_id = "#"  # Channel where submissions go for approval
final_channel_id = "#"     # Channel where approved submissions are posted
```

The user can use the command `/submit_record (level)(completion)(framerate)(username)` 
in any channel, the bot will send it for approval using `approval_channel_id` and once a user with record perms, which is set by `APPROVER_ROLE_NAME` accepts it, it will get send into the final channel `final_channel_id` where it will be logged.

if the record is rejected, the user will get a direct  message from the bot.

