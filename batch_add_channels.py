#!/usr/bin/env python3
"""
Batch script to add multiple YouTube channels efficiently.
This version processes channels in smaller batches to avoid quota issues.
"""

import time
import json
from datetime import datetime
from add_channels import ChannelAdder
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_progress(processed_channels, failed_channels, filename="channel_progress.json"):
    """Save progress to a file"""
    progress = {
        "timestamp": datetime.now().isoformat(),
        "processed": processed_channels,
        "failed": failed_channels,
        "total_processed": len(processed_channels),
        "total_failed": len(failed_channels)
    }
    
    with open(filename, 'w') as f:
        json.dump(progress, f, indent=2)
    
    logger.info(f"Progress saved to {filename}")

def load_progress(filename="channel_progress.json"):
    """Load progress from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"processed": [], "failed": []}

def main():
    # Your channel list
    all_channels = [
        "taletrailz", "SaneRedditor", "burnystories", "redditcackle", "everreddit",
        "eternalreddit", "WinsyTheStory", "TheRedditReader475", "jxlasjournal",
        "marlstories", "redditreads_0", "zlimpy", "EK_stories", "talesyapper",
        "1talesfactory", "borostories", "pulsesttories", "EchoSttoriess",
        "turt_stories", "redditpanther", "storiesclock", "requestedreads",
        "istoryum", "boofstories", "lomustories", "storieslucid", "reddit_report",
        "talereader_0", "taxyclips", "thecoralstories", "unlimited.stories",
        "delilahtales", "pupptalez", "reddityapps", "SA_storybook",
        "redditrewind_02", "SA_reads", "ytminifablefever", "thumbsupstories",
        "thefloam", "jukotexts", "sultan-hakeem", "reddit_gossipz", "cloud9txt",
        "secretdiariessx", "crystallreads", "koalareadss", "randyreads1",
        "creeky_updates", "Zorgowroteit", "ytzexla", "auratext", "creekystoriess",
        "euphraat", "jawerlydiaries", "bjstoriez", "regrethaunts", "truthtide7",
        "redditbiker", "RycoStories", "redditcackle"
    ]
    
    # Load previous progress
    progress = load_progress()
    processed_channels = set(progress.get("processed", []))
    failed_channels = set(progress.get("failed", []))
    
    # Filter out already processed channels
    remaining_channels = [ch for ch in all_channels if ch not in processed_channels and ch not in failed_channels]
    
    if not remaining_channels:
        print("✅ All channels have been processed!")
        print(f"Successfully added: {len(processed_channels)}")
        print(f"Failed to add: {len(failed_channels)}")
        return
    
    print(f"📋 Total channels: {len(all_channels)}")
    print(f"✅ Already processed: {len(processed_channels)}")
    print(f"❌ Previously failed: {len(failed_channels)}")
    print(f"🔄 Remaining to process: {len(remaining_channels)}")
    
    # Process in batches
    batch_size = 10  # Process 10 channels at a time
    adder = ChannelAdder()
    
    try:
        for i in range(0, len(remaining_channels), batch_size):
            batch = remaining_channels[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(remaining_channels) + batch_size - 1) // batch_size
            
            print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} channels)")
            
            for channel_name in batch:
                try:
                    if adder.add_channel_by_name(channel_name):
                        processed_channels.add(channel_name)
                        print(f"✅ Added: {channel_name}")
                    else:
                        failed_channels.add(channel_name)
                        print(f"❌ Failed: {channel_name}")
                        
                except Exception as e:
                    logger.error(f"Error processing {channel_name}: {e}")
                    failed_channels.add(channel_name)
                    print(f"❌ Error: {channel_name}")
                    
                # Small delay between channels
                time.sleep(1)
            
            # Save progress after each batch
            save_progress(list(processed_channels), list(failed_channels))
            
            # Longer delay between batches
            if i + batch_size < len(remaining_channels):
                print("⏳ Taking a break between batches...")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user")
        save_progress(list(processed_channels), list(failed_channels))
    except Exception as e:
        print(f"\n❌ Error: {e}")
        save_progress(list(processed_channels), list(failed_channels))
    finally:
        adder.close()
        
    # Final summary
    print(f"\n🎉 Processing completed!")
    print(f"✅ Successfully added: {len(processed_channels)}")
    print(f"❌ Failed to add: {len(failed_channels)}")
    print(f"📊 Success rate: {(len(processed_channels) / len(all_channels) * 100):.1f}%")
    
    if failed_channels:
        print(f"\n⚠️  Failed channels that need manual attention:")
        for channel in sorted(failed_channels):
            print(f"   - {channel}")

if __name__ == "__main__":
    main() 