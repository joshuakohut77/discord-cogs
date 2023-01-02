class Guard:

    def against_self_plusplus(self, message_author, target_user):
        if message_author == target_user:
            return "You silly goose you can't updoot yourself o_O"
        else:
            return None
