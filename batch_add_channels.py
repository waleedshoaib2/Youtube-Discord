#!/usr/bin/env python3
"""
Batch Add Channels - Add multiple channels efficiently, skipping existing ones
"""

from youtube_monitor import YouTubeMonitor
from database import SessionLocal, Channel
from config import Config
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_add_channels():
    """Add multiple channels in batch, skipping existing ones"""
    print("🚀 BATCH ADD CHANNELS")
    print("=" * 50)
    
    monitor = YouTubeMonitor()
    db = SessionLocal()
    
    # List of channels to add (channel_id, name)
    channels_to_add = [
        ("UCc0nOJerxC8JHf7sg3CK3Vg", "RequestedReads"),  # The real one with 842K subs
        
        # Reddit Story Channels
        ("UCQZ62lRSdnyEXvm8LOfofpA", "taletrailz"),
        ("UCh0IEFKD48ofKDLk4DBg9Lg", "SaneRedditor"),
        ("UC7qeMnSqBoMiHN3uEx_boKA", "burnystories"),
        ("UCQ-PJaqdShIaYidR5RHzJYA", "redditcackle"),
        ("UCS623nmV2oskqvfltlmHugA", "everreddit"),
        ("UCVHB4Gv6fYf8P-lpElxquzg", "eternalreddit"),
        ("UC6ZM1YxI1hBTuBy6R1cBzZw", "WinsyTheStory"),
        ("UCrwlBJAIREbFMJkM5N_vObg", "TheRedditReader475"),
        ("UCcFRuXK8U08uoAVCrvXd28A", "jxlasjournal"),
        ("UCSRglRwew9eAMukKv0BOHBQ", "marlstories"),
        ("UCpvYmWQ1NDHkvxs8erRkZkg", "redditreads_0"),
        ("UCDQvRuXYpvcYmLp-2uZ31Zw", "zlimpy"),
        ("UCWBl3kZaBKPPGcvGu40NMSQ", "EK_stories"),
        ("UCDh6xPSj6_eMPWwCjV2XXdw", "1talesfactory"),
        ("UCAVjwO2qxs0TLt2KEairv1g", "borostories"),
        ("UCWbs1VGto8kcIbQzf6DlrQQ", "pulsesttories"),
        ("UCf6q0_L5u3HO_OqItjwYWyg", "EchoSttoriess"),
        ("UCRV6utfr13xF3Yb3qkQuKSQ", "turt_stories"),
        ("UCycSGDIFNbdMfk4n9N_bZ2w", "redditpanther"),
        ("UC0A7FIRos8eHJtrAFanK7xQ", "storiesclock"),
        ("UC5SFTP2wzPy0ncpSVyuUEHw", "requestedreads"),
        ("UCCo25XUnvzC4URsJrc-O-9w", "istoryum"),
        ("UCh5OLo_LOqi-s1b-qDBcxjA", "boofstories"),
        ("UCarORdtqn-_scYxgn0Fn3hA", "lomustories"),
        ("UCXDtDqcqL2drNxCFXlM_fgQ", "storieslucid"),
        ("UCmOv6mUj7ubA4BIDHM1N1_Q", "reddit_report"),
        ("UCxfN4E6Rrlb2C05Qr1PQqZA", "talereader_0"),
        ("UCihGuKS3GR0RIdHs7_ucmEg", "taxyclips"),
        ("UCcUFguTzjdroXsByRfsBJ0Q", "thecoralstories"),
        ("UCPON8mkipeYL7D3e2r32vIA", "unlimited.stories"),
        ("UCK2AdkNn7YoGHYyz1iESXSw", "delilahtales"),
        ("UC-x_55vxrAjaWtPJd0z4ISw", "pupptalez"),
        ("UC3Vd0OsKY0vEiwZk4urPyPA", "reddityapps"),
        ("UCAcoiJ25aPoagfbhdpNOY7g", "SA_storybook"),
        ("UCks30uLJmsgxcwjQbarMeAA", "redditrewind_02"),
        ("UCg7bGW88j6i-zoUIbugCt4w", "SA_reads"),
        ("UCO3XhGLwFuAbYW_2EHCn9wQ", "ytminifablefever"),
        ("UCBKR2Qe4nCHP1ziUAUTweow", "thumbsupstories"),
        ("UCatTJjYn6q0tQdtnkPrdeyg", "thefloam"),
        ("UC38kOk6onsitxruxg14cKAQ", "jukotexts"),
        ("UClomJuFBz0Gp7uatPwMSt-g", "sultan-hakeem"),
        ("UCy3NvPABrEqsEtk2w_m0ziw", "reddit_gossipz"),
        ("UCmq0xm39NsfofwoD7FbXAEg", "cloud9txt"),
        ("UCDeX3wlGJZ9cdRG1y6xlpvg", "secretdiariessx"),
        ("UCMUVL_63dutA6rXBOtV7A2Q", "crystallreads"),
        ("UCUlkLinLV4_zsMeTcseJ6NQ", "koalareadss"),
        ("UCa5zYvT9RgG839FhUaiAMzg", "randyreads1"),
        ("UCqVQqleLo6ZzRU1oz_iL95Q", "creeky_updates"),
        ("UChu_C4WqR0mtvN1GgqhkGrA", "Zorgowroteit"),
        ("UCLLZhXkJteNtAY5RZ0oGaww", "ytzexla"),
        ("UC7xepvHvPT3OSnUiPr-Wurg", "auratext"),
        ("UCkQPmVNoEwfBS0XG1yDxUVg", "creekystoriess"),
        ("UC9ftOzxQ_X27wxlGlIXbVIg", "euphraat"),
        ("UCq_H3m4A2eFRSkDfxUiJXwg", "jawerlydiaries"),
        ("UCkbXu-7Ix2SpAhWxUk4BpqQ", "bjstoriez"),
        ("UCxhYGJTDq_sSterdt9HTvpw", "regrethaunts"),
        ("UCeDxQ1DELmogZum1c2f_V4Q", "truthtide7"),
        ("UCJWNFuZ_Ljdcess0gnZmlHQ", "redditbiker"),
        ("UCKIBOZN3Tr4XdlnUeUl6XbA", "RycoStories"),
    ]
    
    print(f"📋 Found {len(channels_to_add)} channels to process")
    print()
    
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, (channel_id, channel_name) in enumerate(channels_to_add, 1):
        print(f"🔍 Processing {i}/{len(channels_to_add)}: {channel_name}")
        print(f"   Channel ID: {channel_id}")
        
        # Check if channel already exists
        existing_channel = db.query(Channel).filter_by(channel_id=channel_id).first()
        if existing_channel:
            print(f"   ⏭️  SKIPPED: Channel already exists ({existing_channel.subscriber_count:,} subscribers)")
            skipped_count += 1
            continue
        
        try:
            # Get channel info
            channel_info = monitor.get_channel_info(channel_id)
            
            if channel_info:
                # Create new channel
                channel = Channel(**channel_info)
                db.add(channel)
                db.commit()
                
                print(f"   ✅ ADDED: {channel_info['title']}")
                print(f"      Subscribers: {channel_info['subscriber_count']:,}")
                print(f"      Videos: {channel_info['video_count']:,}")
                added_count += 1
                
            else:
                print(f"   ❌ ERROR: Could not fetch channel info")
                error_count += 1
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            error_count += 1
            db.rollback()
        
        # Rate limiting between requests
        time.sleep(1)
        print()
    
    db.close()
    monitor.close()
    
    print("📊 BATCH SUMMARY:")
    print(f"   ✅ Added: {added_count}")
    print(f"   ⏭️  Skipped: {skipped_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📋 Total processed: {len(channels_to_add)}")
    
    print("\n" + "=" * 50)
    print("✅ Batch add complete!")

def add_requestedreads():
    """Add the real RequestedReads channel"""
    print("🎯 ADDING REQUESTEDREADS")
    print("=" * 50)
    
    monitor = YouTubeMonitor()
    db = SessionLocal()
    
    channel_id = "UCc0nOJerxC8JHf7sg3CK3Vg"
    channel_name = "RequestedReads"
    
    print(f"🔍 Processing: {channel_name}")
    print(f"   Channel ID: {channel_id}")
    
    # Check if channel already exists
    existing_channel = db.query(Channel).filter_by(channel_id=channel_id).first()
    if existing_channel:
        print(f"   ⏭️  SKIPPED: Channel already exists ({existing_channel.subscriber_count:,} subscribers)")
        db.close()
        monitor.close()
        return
    
    try:
        # Get channel info
        channel_info = monitor.get_channel_info(channel_id)
        
        if channel_info:
            # Create new channel
            channel = Channel(**channel_info)
            db.add(channel)
            db.commit()
            
            print(f"   ✅ ADDED: {channel_info['title']}")
            print(f"      Subscribers: {channel_info['subscriber_count']:,}")
            print(f"      Videos: {channel_info['video_count']:,}")
            print(f"      Description: {channel_info['description'][:100]}...")
            
        else:
            print(f"   ❌ ERROR: Could not fetch channel info")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        db.rollback()
    
    db.close()
    monitor.close()
    
    print("\n" + "=" * 50)
    print("✅ RequestedReads add complete!")

if __name__ == "__main__":
    # Add all channels in batch
    batch_add_channels()
    
    # Uncomment to add just RequestedReads
    # add_requestedreads() 