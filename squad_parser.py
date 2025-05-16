import os
import struct
import logging
import mmap
from typing import Dict, List, Any, Optional, BinaryIO

class SquadFile:
    # Magic numbers for different squad file versions
    MAGIC_NUMBERS = [b'FBCH', b'SQDF', b'SQDB', b'SQD2', b'SQIL']
    MAX_SECTION_COUNT = 100
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.countries: Dict[str, List[Any]] = {}
        self.leagues: Dict[str, List[Any]] = {}
        self.teams: Dict[str, List[Any]] = {}
        self.players: Dict[str, List[Any]] = {}
        self.stadiums: Dict[str, List[Any]] = {}
        self.tournaments: Dict[str, List[Any]] = {}
        self.kits: Dict[str, List[Any]] = {}
        self.version: Optional[int] = None
        self.magic: Optional[bytes] = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _read_bytes(self, f: BinaryIO, size: int) -> bytes:
        """Read exact number of bytes"""
        data = f.read(size)
        if len(data) != size:
            raise ValueError(f"Expected {size} bytes, got {len(data)}")
        return data

    def _read_uint32_bytes(self, f: BinaryIO) -> bytes:
        """Read 4 bytes that represent a uint32"""
        return self._read_bytes(f, 4)

    def _bytes_to_uint32(self, data: bytes) -> int:
        """Convert 4 bytes to uint32 safely"""
        if len(data) != 4:
            raise ValueError("Need exactly 4 bytes")
        
        # Try different methods to read the value
        try:
            # Method 1: struct.unpack
            value = struct.unpack('<I', data)[0]
            if value <= 0xFFFFFFFF:
                return value
        except:
            pass
        
        try:
            # Method 2: int.from_bytes
            value = int.from_bytes(data, 'little', signed=False)
            if value <= 0xFFFFFFFF:
                return value
        except:
            pass
        
        try:
            # Method 3: manual unpacking
            value = data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)
            if value <= 0xFFFFFFFF:
                return value
        except:
            pass
        
        # If all methods fail, try to handle overflow
        try:
            # Method 4: handle overflow by masking to 32 bits
            value = (data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)) & 0xFFFFFFFF
            return value
        except Exception as e:
            self.logger.error(f"Failed to convert bytes to uint32: {data.hex()}")
            raise ValueError(f"Invalid uint32 value: {data.hex()}")

    def _validate_squad_file(self, file_path: str) -> bool:
        """Validate squad file format and structure"""
        try:
            with open(file_path, 'rb') as f:
                # Check file size
                file_size = os.path.getsize(file_path)
                if file_size < 12:
                    self.logger.error("File too small to be a valid squad file")
                    return False
                
                # Read and check magic number
                magic = f.read(4)
                if magic not in self.MAGIC_NUMBERS:
                    self.logger.error(f"Invalid magic number: {magic!r}")
                    return False
                
                # Read version
                version_bytes = f.read(4)
                try:
                    version = struct.unpack('<I', version_bytes)[0]
                    if not 0 <= version <= 1000:
                        self.logger.warning(f"Unusual version number: {version}")
                except struct.error:
                    self.logger.error("Failed to read version number")
                    return False
                
                # Read section count
                section_count_bytes = f.read(4)
                try:
                    section_count = struct.unpack('<I', section_count_bytes)[0]
                    if not 0 <= section_count <= self.MAX_SECTION_COUNT:
                        self.logger.error(f"Invalid section count: {section_count}")
                        return False
                except struct.error:
                    self.logger.error("Failed to read section count")
                    return False
                
                # Try to read section table
                try:
                    for i in range(section_count):
                        section_type = struct.unpack('<I', f.read(4))[0]
                        section_offset = struct.unpack('<I', f.read(4))[0]
                        section_size = struct.unpack('<I', f.read(4))[0]
                        
                        # Validate section bounds
                        if section_offset + section_size > file_size:
                            self.logger.error(f"Section {i} extends beyond file bounds")
                            return False
                        
                        # Skip padding
                        f.read(4)
                except struct.error:
                    self.logger.error(f"Failed to read section table entry {i}")
                    return False
                except Exception as e:
                    self.logger.error(f"Error validating section table: {str(e)}")
                    return False
                
                self.logger.info("Squad file validation successful")
                return True
                
        except Exception as e:
            self.logger.error(f"Error validating squad file: {str(e)}")
            return False
    
    def _dump_file_header(self, file_path: str) -> None:
        """Dump the first 64 bytes of the file for analysis"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(64)
                self.logger.info("File header dump:")
                for i in range(0, len(header), 16):
                    chunk = header[i:i+16]
                    hex_dump = ' '.join(f'{b:02x}' for b in chunk)
                    ascii_dump = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
                    self.logger.info(f"{i:04x}: {hex_dump:48} | {ascii_dump}")
        except Exception as e:
            self.logger.error(f"Failed to dump file header: {str(e)}")

    def _read_uint32_safe(self, f: BinaryIO) -> int:
        """Read an unsigned 32-bit integer safely"""
        data = f.read(4)
        if len(data) != 4:
            raise ValueError(f"Expected 4 bytes for uint32, got {len(data)}")
        
        # Try different methods to read the value
        methods = [
            lambda: struct.unpack('<I', data)[0],  # Little-endian
            lambda: struct.unpack('>I', data)[0],  # Big-endian
            lambda: int.from_bytes(data, 'little'),  # Alternative little-endian
            lambda: int.from_bytes(data, 'big'),  # Alternative big-endian
            lambda: data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24),  # Manual little-endian
            lambda: data[3] | (data[2] << 8) | (data[1] << 16) | (data[0] << 24)   # Manual big-endian
        ]
        
        errors = []
        for method in methods:
            try:
                value = method()
                if 0 <= value <= 0xFFFFFFFF:
                    return value
            except Exception as e:
                errors.append(str(e))
        
        # If we get here, all methods failed
        self.logger.error(f"Failed to read uint32 at offset 0x{f.tell()-4:08x}")
        self.logger.error(f"Raw bytes: {' '.join(f'{b:02x}' for b in data)}")
        self.logger.error(f"Errors: {', '.join(errors)}")
        raise ValueError("Could not safely read uint32 value")

    def load(self):
        """Load data from squad file"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Squad file not found: {self.file_path}")
        
        file_size = os.path.getsize(self.file_path)
        if file_size < 12:
            raise ValueError(f"File too small to be valid: {file_size} bytes")
        
        with open(self.file_path, 'rb') as f:
            try:
                # Read magic number
                self.magic = self._read_bytes(f, 4)
                if self.magic not in self.MAGIC_NUMBERS:
                    self.logger.error(f"Invalid magic number: {self.magic!r}")
                    self.logger.error(f"Expected one of: {[m.decode('ascii', 'ignore') for m in self.MAGIC_NUMBERS]}")
                    raise ValueError("Invalid squad file format")
                
                self.logger.info(f"Detected file format: {self.magic.decode('ascii', 'ignore')}")
                
                # Read version
                version_bytes = self._read_uint32_bytes(f)
                try:
                    self.version = self._bytes_to_uint32(version_bytes)
                    if not 0 <= self.version <= 1000:
                        self.logger.warning(f"Unusual version number: {self.version}")
                except ValueError as e:
                    self.logger.error(f"Invalid version number bytes: {version_bytes.hex()}")
                    raise
                
                # Read section count
                section_count_bytes = self._read_uint32_bytes(f)
                try:
                    section_count = self._bytes_to_uint32(section_count_bytes)
                    if not 0 <= section_count <= self.MAX_SECTION_COUNT:
                        self.logger.error(f"Invalid section count: {section_count}")
                        self.logger.error(f"Section count bytes: {section_count_bytes.hex()}")
                        raise ValueError(f"Section count must be between 0 and {self.MAX_SECTION_COUNT}")
                except ValueError as e:
                    self.logger.error(f"Invalid section count bytes: {section_count_bytes.hex()}")
                    raise
                
                self.logger.info(f"File version: {self.version}, sections: {section_count}")
                
                # Read section table
                sections = []
                for i in range(section_count):
                    try:
                        # Read section header
                        type_bytes = self._read_uint32_bytes(f)
                        offset_bytes = self._read_uint32_bytes(f)
                        size_bytes = self._read_uint32_bytes(f)
                        self._read_bytes(f, 4)  # Skip padding
                        
                        # Convert bytes to integers with validation
                        try:
                            section_type = self._bytes_to_uint32(type_bytes)
                            section_offset = self._bytes_to_uint32(offset_bytes)
                            section_size = self._bytes_to_uint32(size_bytes)
                            
                            # Validate section bounds
                            if section_offset > file_size:
                                raise ValueError(f"Section offset {section_offset} beyond file size {file_size}")
                            if section_size > file_size - section_offset:
                                raise ValueError(f"Section size {section_size} too large for offset {section_offset}")
                            
                            sections.append((section_type, section_offset, section_size))
                            self.logger.info(f"Section {i}: type=0x{section_type:02x}, offset=0x{section_offset:08x}, size={section_size}")
                            
                        except ValueError as e:
                            self.logger.error(f"Invalid section {i} header:")
                            self.logger.error(f"  Type bytes: {type_bytes.hex()}")
                            self.logger.error(f"  Offset bytes: {offset_bytes.hex()}")
                            self.logger.error(f"  Size bytes: {size_bytes.hex()}")
                            raise ValueError(f"Invalid section {i} header: {str(e)}")
                            
                    except Exception as e:
                        self.logger.error(f"Error reading section {i} header: {str(e)}")
                        raise
                
                # Process sections
                for i, (section_type, offset, size) in enumerate(sections):
                    try:
                        f.seek(offset)
                        
                        # Read section data in chunks
                        section_data = bytearray()
                        remaining = size
                        chunk_size = 1024 * 1024  # 1MB chunks
                        
                        while remaining > 0:
                            to_read = min(remaining, chunk_size)
                            chunk = self._read_bytes(f, to_read)
                            section_data.extend(chunk)
                            remaining -= to_read
                        
                        self._parse_section(section_type, bytes(section_data))
                        
                    except Exception as e:
                        self.logger.error(f"Error processing section {i}: {str(e)}")
                        raise
                
            except Exception as e:
                self.logger.error(f"Error reading squad file: {str(e)}")
                raise
    
    def _parse_section(self, section_type: int, data: bytes) -> None:
        """Parse a section of the squad file"""
        try:
            if len(data) == 0:
                self.logger.warning(f"Empty section type 0x{section_type:02x}")
                return
            
            self.logger.debug(f"Parsing section type 0x{section_type:02x} with {len(data)} bytes")
            
            if section_type == 0x01:  # Teams
                self._parse_teams_section(data)
            elif section_type == 0x02:  # Players
                self._parse_players_section(data)
            elif section_type == 0x03:  # Leagues
                self._parse_leagues_section(data)
            elif section_type == 0x04:  # Nations
                self._parse_countries_section(data)
            else:
                self.logger.warning(f"Unknown section type: 0x{section_type:02x}")
        except Exception as e:
            self.logger.error(f"Error parsing section type 0x{section_type:02x}: {str(e)}")
            raise
    
    def _parse_teams_section(self, data: bytes) -> None:
        """Parse teams section data"""
        offset = 0
        while offset + 4 <= len(data):
            try:
                # Read team ID
                team_id = struct.unpack_from('<I', data, offset)[0]
                offset += 4
                
                # Read name length
                if offset >= len(data):
                    break
                name_len = data[offset]
                offset += 1
                
                # Read name
                if offset + name_len > len(data):
                    self.logger.error(f"Team name extends beyond section bounds")
                    break
                
                try:
                    name = data[offset:offset+name_len].decode('utf-8')
                except UnicodeDecodeError:
                    name = data[offset:offset+name_len].decode('latin1')
                
                offset += name_len
                
                # Store team data
                self.teams[str(team_id)] = [name]
                self.logger.debug(f"Parsed team: ID={team_id}, Name={name}")
                
            except Exception as e:
                self.logger.error(f"Error parsing team at offset {offset}: {str(e)}")
                break
    
    def _parse_players_section(self, data: bytes) -> None:
        """Parse players section data"""
        offset = 0
        while offset + 8 <= len(data):
            try:
                # Read player ID and data size
                player_id, data_size = struct.unpack_from('<II', data, offset)
                offset += 8
                
                if offset + data_size > len(data):
                    self.logger.error(f"Player data extends beyond section bounds")
                    break
                
                # Process player data
                player_data = self._process_player_data(data[offset:offset+data_size])
                if player_data:
                    self.players[str(player_id)] = player_data
                    self.logger.debug(f"Parsed player: ID={player_id}")
                
                offset += data_size
                
            except Exception as e:
                self.logger.error(f"Error parsing player at offset {offset}: {str(e)}")
                break
    
    def _parse_countries_section(self, data: bytes) -> None:
        """Parse countries section data"""
        offset = 0
        while offset < len(data):
            try:
                # Read country ID (4 bytes)
                country_id = struct.unpack_from('<I', data, offset)[0]
                offset += 4
                
                # Read name length and name
                name_len = data[offset]
                offset += 1
                name = data[offset:offset+name_len].decode('latin1')
                offset += name_len
                
                # Read short name length and short name
                short_name_len = data[offset]
                offset += 1
                short_name = data[offset:offset+short_name_len].decode('latin1')
                offset += short_name_len
                
                # Read fixed fields
                abbrev = data[offset:offset+3].decode('latin1')
                offset += 3
                confederation = data[offset:offset+8].decode('latin1').rstrip('\x00')
                offset += 8
                iso_code = data[offset:offset+6].decode('latin1').rstrip('\x00')
                offset += 6
                level = data[offset]
                offset += 1
                rating = data[offset]
                offset += 1
                flag_code = data[offset:offset+3].decode('latin1')
                offset += 3
                
                self.countries[str(country_id)] = [
                    name, short_name, abbrev, confederation,
                    iso_code, str(level), str(rating), flag_code
                ]
                
            except Exception as e:
                self.logger.error(f"Error parsing country at offset {offset}: {str(e)}")
                break
    
    def _parse_leagues_section(self, data: bytes) -> None:
        """Parse leagues section data"""
        # Similar structure to countries section
        pass
    
    def save(self):
        """Save data to squad file"""
        with open(self.file_path, 'wb') as f:
            try:
                if self.magic == b'FBCH':
                    self._save_fc25_format(f)
                else:
                    self._save_legacy_format(f)
            except Exception as e:
                raise ValueError(f"Error saving squad file: {str(e)}")
    
    def _save_fc25_format(self, f):
        """Save in FC 25 format"""
        # Write header
        f.write(b'FBCH')
        self._write_uint32(f, self.version or 1)
        
        # Write file size and padding
        size_pos = f.tell()
        self._write_uint32(f, 0)  # Placeholder for file size
        self._write_uint32(f, 0)  # Padding
        
        # Count sections to write
        sections = [
            (0x01, self.teams),
            (0x02, self.players),
            (0x03, self.leagues),
            (0x04, self.countries)
        ]
        active_sections = [(type_id, data) for type_id, data in sections if data]
        
        # Write section count
        self._write_uint32(f, len(active_sections))
        
        # Write section table
        section_table_pos = f.tell()
        for section_type, _ in active_sections:
            self._write_uint32(f, section_type)
            self._write_uint32(f, 0)  # Placeholder for offset
            self._write_uint32(f, 0)  # Placeholder for size
            self._write_uint32(f, 0)  # Padding
        
        # Write each section
        for i, (section_type, section_data) in enumerate(active_sections):
            section_offset = f.tell()
            section_start = f.tell()
            
            # Convert and write section data
            if section_type == 0x01:
                self._write_fc25_teams(f, section_data)
            elif section_type == 0x02:
                self._write_fc25_players(f, section_data)
            elif section_type == 0x03:
                self._write_fc25_leagues(f, section_data)
            elif section_type == 0x04:
                self._write_fc25_nations(f, section_data)
            
            section_size = f.tell() - section_start
            
            # Update section table
            f.seek(section_table_pos + (i * 16) + 4)
            self._write_uint32(f, section_offset)
            self._write_uint32(f, section_size)
            f.seek(0, 2)  # Seek to end
        
        # Update file size
        total_size = f.tell()
        f.seek(size_pos)
        self._write_uint32(f, total_size)
    
    def _save_legacy_format(self, f):
        """Save in legacy format"""
        # Write file header
        f.write(self.magic or b'SQDF')
        f.write(struct.pack('<I', self.version or 1))
        
        # Count sections
        sections = [
            (1, self.countries),
            (2, self.leagues),
            (3, self.teams),
            (4, self.players),
            (5, self.stadiums),
            (6, self.tournaments),
            (7, self.kits)
        ]
        active_sections = [(type_id, data) for type_id, data in sections if data]
        
        # Write section count
        f.write(struct.pack('<I', len(active_sections)))
        
        # Write each section
        for section_type, section_data in active_sections:
            self._write_legacy_section(f, section_type, section_data)
    
    def _write_fc25_teams(self, f, teams):
        """Write teams in FC 25 format"""
        for team_id, data in teams.items():
            # Write team ID
            self._write_uint32(f, int(team_id))
            
            # Write name
            name_bytes = data[0].encode('utf-8')
            f.write(bytes([len(name_bytes)]))
            f.write(name_bytes)
    
    def _write_fc25_players(self, f, players):
        """Write players in FC 25 format"""
        # Similar to teams
        pass
    
    def _write_fc25_leagues(self, f, leagues):
        """Write leagues in FC 25 format"""
        # Similar to teams
        pass
    
    def _write_fc25_nations(self, f, nations):
        """Write nations in FC 25 format"""
        # Similar to teams
        pass
    
    def _write_legacy_section(self, f, section_type, data):
        """Write a section in legacy format"""
        try:
            # Convert section data to binary
            binary_data = self._convert_section_to_binary(section_type, data)
            
            # Write section header
            f.write(struct.pack('<I', section_type))
            f.write(struct.pack('<I', len(binary_data)))
            
            # Write section data
            f.write(binary_data)
            
        except Exception as e:
            raise ValueError(f"Error writing section {section_type}: {str(e)}")
    
    def _convert_section_to_binary(self, section_type, data):
        """Convert section data to binary format"""
        if section_type == 1:  # Countries
            return self._convert_countries_to_binary(data)
        # Add other section conversions as needed
        return b''
    
    def _convert_countries_to_binary(self, countries):
        """Convert countries data to binary format"""
        binary_data = bytearray()
        for country_id, data in countries.items():
            # Write country ID
            binary_data.extend(struct.pack('<I', int(country_id)))
            
            # Write name
            name_bytes = data[0].encode('latin1')
            binary_data.append(len(name_bytes))
            binary_data.extend(name_bytes)
            
            # Write short name
            short_name_bytes = data[1].encode('latin1')
            binary_data.append(len(short_name_bytes))
            binary_data.extend(short_name_bytes)
            
            # Write fixed fields
            binary_data.extend(data[2].encode('latin1'))  # Abbreviation (3 chars)
            binary_data.extend(data[3].ljust(8, '\x00').encode('latin1'))  # Confederation
            binary_data.extend(data[4].ljust(6, '\x00').encode('latin1'))  # ISO code
            binary_data.append(int(data[5]))  # Level
            binary_data.append(int(data[6]))  # Rating
            binary_data.extend(data[7].encode('latin1'))  # Flag code (3 chars)
            
        return binary_data
    
    # Getter methods remain unchanged
    def get_countries(self):
        """Get all countries"""
        return self.countries
    
    def update_country(self, country_id, data):
        """Update country data"""
        self.countries[country_id] = data
        self.save()
    
    def get_leagues(self):
        """Get all leagues"""
        return self.leagues
    
    def get_teams(self):
        """Get all teams"""
        return self.teams
    
    def get_players(self):
        """Get all players"""
        return self.players
        
    def get_stadiums(self):
        """Get all stadiums"""
        return self.stadiums
        
    def get_tournaments(self):
        """Get all tournaments"""
        return self.tournaments
        
    def get_kits(self):
        """Get all kits"""
        return self.kits 