from voting.models import Vote

def verify_election_blockchain(election):
    """
    Traverses the votes for an election to ensure the blockchain is intact.
    Returns True if safe, Returns False and the broken Vote ID if hacked.
    """
    votes = Vote.objects.filter(election=election).order_by('id')
    
    if not votes.exists():
        return True, "No votes yet."

    previous_hash_check = "0" * 64

    for vote in votes:
        # 1. Check if link to previous block is broken
        if vote.previous_hash != previous_hash_check:
            return False, f"Chain broken at Vote ID {vote.id}: Previous hash mismatch!"

        # 2. Check if current block data was tampered with
        expected_hash = vote.generate_hash()
        if vote.block_hash != expected_hash:
            return False, f"Data tampered at Vote ID {vote.id}: Block hash invalid!"

        previous_hash_check = vote.block_hash

    return True, "Blockchain is intact and secure."