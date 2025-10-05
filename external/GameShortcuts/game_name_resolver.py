#!/usr/bin/env python3
"""
Game Name Resolver
Maps abbreviated game names to full names using common game databases.
"""

import json
from pathlib import Path

class GameNameResolver:
    def __init__(self):
        self.game_mappings = self.load_game_mappings()
        
    def load_game_mappings(self):
        """Load comprehensive game name mappings."""
        return {
            # Elder Scrolls Series
            'SkyrimSE': 'The Elder Scrolls V: Skyrim Special Edition',
            'Skyrim': 'The Elder Scrolls V: Skyrim',
            'Morrowind': 'The Elder Scrolls III: Morrowind',
            'Oblivion': 'The Elder Scrolls IV: Oblivion',
            
            # Battlefield Series
            'bf4': 'Battlefield 4',
            'bf3': 'Battlefield 3',
            'bf1': 'Battlefield 1',
            'bfv': 'Battlefield V',
            'bf2042': 'Battlefield 2042',
            
            # Ghost Recon Series
            'GRW': 'Tom Clancy\'s Ghost Recon Wildlands',
            'GSS2': 'Tom Clancy\'s Ghost Recon Wildlands',
            'Ghost Recon Wildlands': 'Tom Clancy\'s Ghost Recon Wildlands',
            
            # Halo Series
            'MCC-Win64-Shipping': 'Halo: The Master Chief Collection',
            'HaloWars2_WinAppDX12Final': 'Halo Wars 2',
            'MCC': 'Halo: The Master Chief Collection',
            
            # FromSoftware Games
            'eldenring': 'Elden Ring',
            'DarkSouls3': 'Dark Souls III',
            'DarkSouls2': 'Dark Souls II',
            'DarkSouls': 'Dark Souls',
            'Sekiro': 'Sekiro: Shadows Die Twice',
            
            # Rockstar Games
            'PlayRDR2': 'Red Dead Redemption 2',
            'RDR2': 'Red Dead Redemption 2',
            'GTA5': 'Grand Theft Auto V',
            'GTA4': 'Grand Theft Auto IV',
            
            # Ubisoft Games
            'LANoire': 'L.A. Noire',
            'ACValhalla': 'Assassin\'s Creed Valhalla',
            'ACOdyssey': 'Assassin\'s Creed Odyssey',
            'ACOrigins': 'Assassin\'s Creed Origins',
            
            # Indie Games
            'Stardew Valley': 'Stardew Valley',
            'Terraria': 'Terraria',
            'Minecraft': 'Minecraft',
            'Among Us': 'Among Us',
            
            # Strategy Games
            'stellaris': 'Stellaris',
            'Civ6': 'Sid Meier\'s Civilization VI',
            'Civ5': 'Sid Meier\'s Civilization V',
            'TotalWar': 'Total War',
            
            # RPG Games
            'underrail': 'Underrail',
            'openmw': 'OpenMW',
            'thief': 'Thief',
            'castle': 'Castle',
            
            # Final Fantasy Series
            'ff2': 'Final Fantasy II',
            'ff7': 'Final Fantasy VII',
            'ff8': 'Final Fantasy VIII',
            'ff9': 'Final Fantasy IX',
            'ff10': 'Final Fantasy X',
            'ff15': 'Final Fantasy XV',
            
            # Other Popular Games
            'rfg': 'Red Faction Guerrilla',
            'slavania': 'Slavania',
            'ixs': 'IXS',
            'noop': 'Noop',
            'lhb': 'LHB',
            'anuket_x64': 'Anuket',
            'dy_login_tool': 'DY Login Tool',
            'BsSndRpt': 'BS Sound Report',
            'CaptiveAppEntry': 'Captive App Entry',
            'cataclysm-tiles': 'Cataclysm: Dark Days Ahead',
            'CelebrityPoker': 'Celebrity Poker',
            'Centum': 'Centum',
            'Chess2': 'Chess 2',
            'cmark': 'CMark',
            'ColonyShipGame': 'Colony Ship',
            'Cronos': 'Cronos',
            'CryptMaster': 'Crypt Master',
            'DarkFuture': 'Dark Future',
            'deadrising2otr': 'Dead Rising 2: Off the Record',
            'despelote': 'Despelote',
            'DistantWorlds2': 'Distant Worlds 2',
            'Duskers': 'Duskers',
            'Dust Raiders': 'Dust Raiders',
            'Dwarf Fortress': 'Dwarf Fortress',
            'EvilWest': 'Evil West',
            'Expedition33_Steam': 'Expedition 33',
            'FactoryGameSteam': 'Satisfactory',
            'FightingFantasy': 'Fighting Fantasy',
            'Frostpunk2': 'Frostpunk 2',
            'Game': 'Game',
            'GhostOfTsushima': 'Ghost of Tsushima',
            'gorky17': 'Gorky 17',
            'Gremlins_Inc': 'Gremlins Inc',
            'Grickle101': 'Grickle 101',
            'Grickle102': 'Grickle 102',
            'Guild3': 'The Guild 3',
            'Gwent': 'Gwent',
            'Hand of Fate 2': 'Hand of Fate 2',
            'hathor_Shipping_Playfab_Steam_x64': 'Hathor',
            'Hive': 'Hive',
            'HYPERVIOLENT': 'Hyperviolent',
            'Inscryption': 'Inscryption',
            'JustCause3': 'Just Cause 3',
            'Khet': 'Khet',
            'Konung2': 'Konung 2',
            'Lara Croft GO': 'Lara Croft GO',
            'Last Call BBS': 'Last Call BBS',
            'Lightning': 'Lightning',
            'likeadragon8': 'Like a Dragon 8',
            'LOP': 'LOP',
            'Lord of the Rings - LCG': 'Lord of the Rings: Living Card Game',
            'LoveLetter_Release': 'Love Letter',
            'McPixel3': 'McPixel 3',
            'ModEngine-2.1.0.0-win64': 'ModEngine',
            'Mysterium': 'Mysterium',
            'NotForBroadcast': 'Not For Broadcast',
            'OneDeckDungeon': 'One Deck Dungeon',
            'Pandemic': 'Pandemic',
            'Patch Quest': 'Patch Quest',
            'PICAYUNEDREAMS': 'Picayune Dreams',
            'Pinball FX3': 'Pinball FX3',
            'PinballArcade': 'Pinball Arcade',
            'PinballM': 'Pinball M',
            'Planet Crafter': 'Planet Crafter',
            'PokerNight2': 'Poker Night 2',
            'Precinct': 'Precinct',
            'Project Warlock 2': 'Project Warlock 2',
            'ProjetCaillou': 'Projet Caillou',
            'QtWebEngineProcess': 'Qt Web Engine Process',
            'Racine': 'Racine',
            'Rack and Slay': 'Rack and Slay',
            'RainWorld': 'Rain World',
            'Ratropolis': 'Ratropolis',
            'Roadwarden-32': 'Roadwarden',
            'Schedule I': 'Schedule I',
            'Sentinels': 'Sentinels',
            'SHB': 'SHB',
            'Shenzhen': 'Shenzhen I/O',
            'SlimeRancher2': 'Slime Rancher 2',
            'Splendor': 'Splendor',
            'starrealms': 'Star Realms',
            'SuchArt': 'SuchArt',
            'Super Lone Survivor': 'Super Lone Survivor',
            'Suzerain': 'Suzerain',
            'Tabletop Simulator': 'Tabletop Simulator',
            'TabletopCreator': 'Tabletop Creator',
            'TabletopPlayground': 'Tabletop Playground',
            'Tainted Grail': 'Tainted Grail',
            'TalesAndTactics': 'Tales and Tactics',
            'Talisman': 'Talisman',
            'Tempest': 'Tempest',
            'TerraformingMars': 'Terraforming Mars',
            'The Warlock of Firetop Mountain': 'The Warlock of Firetop Mountain',
            'TheInnSanity': 'The Inn Sanity',
            'TheNecromancer': 'The Necromancer',
            'TheQuarry': 'The Quarry',
            'TheThaumaturge': 'The Thaumaturge',
            'TheWitcherAdventureGame': 'The Witcher Adventure Game',
            'Tiny Terry\'s Turbo Trip': 'Tiny Terry\'s Turbo Trip',
            'TOEM': 'TOEM',
            'Toy Shire': 'Toy Shire',
            'TwilightStruggle': 'Twilight Struggle',
            'Ultros': 'Ultros',
            'Uncanny Tales 1992': 'Uncanny Tales 1992',
            'Vortex': 'Vortex',
            'Warhammer 40,000 Boltgun': 'Warhammer 40,000: Boltgun',
            'WhosLila': 'Who\'s Lila',
            'Wingspan': 'Wingspan',
            'WorshippersOfCthulhu': 'Worshippers of Cthulhu',
            'YKS': 'YKS'
        }
        
    def resolve_game_name(self, name):
        """Resolve abbreviated game name to full name."""
        # Direct mapping
        if name in self.game_mappings:
            return self.game_mappings[name]
            
        # Try case-insensitive matching
        name_lower = name.lower()
        for key, value in self.game_mappings.items():
            if key.lower() == name_lower:
                return value
                
        # Try partial matching for common patterns
        if name_lower.startswith('launch '):
            clean_name = name.replace('Launch ', '').strip()
            return self.resolve_game_name(clean_name)
            
        # Return original name if no match found
        return name
        
    def get_game_info(self, name):
        """Get additional game information."""
        resolved_name = self.resolve_game_name(name)
        
        # Add some basic genre information based on common patterns
        genre_hints = []
        name_lower = resolved_name.lower()
        
        if any(word in name_lower for word in ['strategy', 'civilization', 'total war', 'stellaris']):
            genre_hints.append('Strategy')
        elif any(word in name_lower for word in ['rpg', 'role-playing', 'elder scrolls', 'fallout']):
            genre_hints.append('RPG')
        elif any(word in name_lower for word in ['shooter', 'fps', 'battlefield', 'call of duty']):
            genre_hints.append('Shooter')
        elif any(word in name_lower for word in ['simulation', 'sim', 'city', 'tycoon']):
            genre_hints.append('Simulation')
        elif any(word in name_lower for word in ['puzzle', 'puzzle', 'tetris', 'sudoku']):
            genre_hints.append('Puzzle')
        elif any(word in name_lower for word in ['racing', 'drive', 'car', 'motor']):
            genre_hints.append('Racing')
        elif any(word in name_lower for word in ['sports', 'football', 'soccer', 'basketball']):
            genre_hints.append('Sports')
        elif any(word in name_lower for word in ['fighting', 'street fighter', 'tekken', 'mortal kombat']):
            genre_hints.append('Fighting')
        elif any(word in name_lower for word in ['platform', 'mario', 'sonic', 'crash']):
            genre_hints.append('Platformer')
        elif any(word in name_lower for word in ['adventure', 'point and click', 'myst']):
            genre_hints.append('Adventure')
        elif any(word in name_lower for word in ['horror', 'resident evil', 'silent hill', 'fear']):
            genre_hints.append('Horror')
        elif any(word in name_lower for word in ['action', 'adventure', 'tomb raider', 'uncharted']):
            genre_hints.append('Action-Adventure')
            
        return {
            'resolved_name': resolved_name,
            'original_name': name,
            'genre_hints': genre_hints
        }


def main():
    resolver = GameNameResolver()
    
    test_names = ['SkyrimSE', 'bf4', 'MCC-Win64-Shipping', 'eldenring', 'PlayRDR2']
    print('Game Name Resolution Test:')
    for name in test_names:
        info = resolver.get_game_info(name)
        print(f'{name} -> {info["resolved_name"]} (Genres: {", ".join(info["genre_hints"])})')


if __name__ == "__main__":
    main()
