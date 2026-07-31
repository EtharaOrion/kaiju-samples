# Implement `JulianSchmid/etherparse`

You are given a Rust repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that calls `todo!()` (or `unimplemented!()`) on invocation.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, traits, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `JulianSchmid/etherparse`
- Source directory to implement: `etherparse/src/`
- Test command: `` (run against ``)
- Specification / docs: 

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

A zero allocation supporting library for parsing & writing a bunch of packet based protocols (EthernetII, IPv4, IPv6, UDP, TCP …).

Currently supported are: Ethernet II IEEE 802.1Q VLAN Tagging Header MACsec (IEEE 802.1AE) ARP IPv4 IPv6 (supporting the most common extension headers, but not all) UDP TCP ICMP & ICMPv6 (not all message types are supported) Reconstruction of fragmented IP packets is also supported, but requires allocations.

Usage Add the following to your Cargo.toml : What is etherparse?

Etherparse is intended to provide the basic network parsing functions that allow for easy analysis, transformation or generation of recorded network data.

Some key points are: It is completely written in Rust and thoroughly tested.

Special attention has been paid to not use allocations or syscalls.

The package is still in development and can & will still change.

The current focus of development is on the most popular protocols in the internet & transport layer.

How to parse network packages?

[dependencies] etherparse = "0.20.3" Etherparse gives you two options for parsing network packages automatically: Slicing the packet Here the different components in a packet are separated without parsing all their fields. For each header a slice is generated that allows access to the fields of a header.

This is the faster option if your code is not interested in all fields of all the headers. It is a good choice if you just want filter or find packages based on a subset of the headers and/or their fields.

Depending from which point downward you want to slice a package check out the functions: SlicedPacket::from_ethernet for parsing from an Ethernet II header downwards SlicedPacket::from_linux_sll for parsing from a Linux Cooked Capture v1 (SLL) downwards SlicedPacket::from_ether_type for parsing a slice starting after an Ethernet II header SlicedPacket::from_ip for parsing from an IPv4 or IPv6 downwards In case you want to parse cut off packets (e.g. packets returned in in ICMP message) you can use the “lax” parsing methods: LaxSlicedPacket::from_ethernet for parsing from an Ethernet II header downwards LaxSlicedPacket::from_ether_type for parsing a slice starting after an Ethernet II header LaxSlicedPacket::from_ip for parsing from an IPv4 or IPv6 downwards Deserializing all headers into structs This option deserializes all known headers and transfers their contents to header structs.

match SlicedPacket::from_ethernet(&packet) { Err(value) => println!("Err {:?}", value), Ok(value) => { println!("link: {:?}", value.link); println!("link_exts: {:?}", value.link_exts); // contains vlan & ma println!("net: {:?}", value.net); // contains ip & arp println!("transport: {:?}", value.transport); } }; match PacketHeaders::from_ethernet_slice(&packet) { Err(value) => println!("Err {:?}", value), Ok(value) => { println!("link: {:?}", value.link); println!("link_exts: {:?}", value.link_exts); // contains vlan & ma println!("net: {:?}", value.net); // contains ip & arp println!("transport: {:?}", value.transport); This option is slower then slicing when only few fields are accessed. But it can be the faster option or useful if you are interested in most fields anyways or if you want to re-serialize the headers with modified values.

Depending from which point downward you want to unpack a package check out the functions PacketHeaders::from_ethernet_slice for parsing from an Ethernet II header downwards PacketHeaders::from_ether_type for parsing a slice starting after an Ethernet II header PacketHeaders::from_ip_slice for parsing from an IPv4 or IPv6 downwards In case you want to parse cut off packets (e.g. packets returned in in ICMP message) you can use the “lax” parsing methods: LaxPacketHeaders::from_ethernet for parsing from an Ethernet II header downwards LaxPacketHeaders::from_ether_type for parsing a slice starting after an Ethernet II header LaxPacketHeaders::from_ip for parsing from an IPv4 or IPv6 downwards Manually slicing only one packet layer It is also possible to only slice one packet layer: Ethernet2Slice::from_slice_without_fcs & Ethernet2Slice::from_slice_with_crc32_fcs LinuxSllSlice::from_slice SingleVlanSlice::from_slice MacsecSlice::from_slice IpSlice::from_slice & LaxIpSlice::from_slice Ipv4Slice::from_slice & LaxIpv4Slice::from_slice Ipv6Slice::from_slice & LaxIpv6Slice::from_slice UdpSlice::from_slice & UdpSlice::from_slice_lax TcpSlice::from_slice Icmpv4Slice::from_slice Icmpv6Slice::from_slice The resulting data types allow access to both the header(s) and the payload of the layer and will automatically limit the length of payload if the layer has a length field limiting the payload (e.g. the payload of IPv6 packets will be limited by the “payload length” field in an IPv6 header).

Packet Builder The PacketBuilder struct provides a high level interface for quickly creating network packets. The PacketBuilder will automatically set fields which can be deduced from the content and compositions of the packet itself (e.g. checksums, lengths, ethertype, ip protocol number).

Example: There is also an example for TCP packets available.

Check out the PacketBuilder documentation for more information.

Manually serializing each header Alternatively it is possible to manually build a packet (example). Generally each struct representing a header has a “write” method that allows it to be serialized. These write methods sometimes automatically calculate checksums and fill them in. In case this is unwanted behavior (e.g. if you want to generate a packet with an invalid checksum), it is also possible to call a “write_raw” method that will simply serialize the data without doing checksum calculations.

Read the documentations of the different methods for a more details: Ethernet2Header::to_bytes & Ethernet2Header::write LinuxSllHeader::to_bytes & LinuxSllHeader::write use etherparse::PacketBuilder; let builder = PacketBuilder:: ethernet2([1,2,3,4,5,6], //source mac [7,8,9,10,11,12]) //destination mac .ipv4([192,168,1,1], //source ip [192,168,1,2], //destination ip 20) //time to life .udp(21, //source port 1234); //destination port //payload of the udp packet let payload = [1,2,3,4,5,6,7,8]; //get some memory to store the result let mut result = Vec::<u8>::with_capacity(builder.size(payload.len())); //serialize //this will automatically set all length fields, checksums and identifiers //before writing the packet out to "result" builder.write(&mut result, &payload).unwrap(); SingleVlanHeader::to_bytes & SingleVlanHeader::write MacsecHeader::to_bytes & MacsecHeader::write ArpPacket::to_bytes & ArpPacket::write ArpEthIpv4Packet::to_bytes Ipv4Header::to_bytes & Ipv4Header::write & Ipv4Header::write_raw Ipv4Extensions::write Ipv6Header::to_bytes & Ipv6Header::write Ipv6Extensions::write Ipv6RawExtHeader::to_bytes & Ipv6RawExtHeader::write IpAuthHeader::to_bytes & IpAuthHeader::write Ipv6FragmentHeader::to_bytes & Ipv6FragmentHeader::write UdpHeader::to_bytes & UdpHeader::write TcpHeader::to_bytes & TcpHeader::write Icmpv4Header::to_bytes & Icmpv4Header::write Icmpv6Header::to_bytes & Icmpv6Header::write References Darpa Internet Program Protocol Specification RFC 791 Internet Protocol, Version 6 (IPv6) Specification RFC 8200 IANA 802 EtherTypes IANA Protocol Numbers Internet Protocol Version 6 (IPv6) Parameters Wikipedia IEEE_802.1Q User Datagram Protocol (UDP) RFC 768 Transmission Control Protocol RFC 793 TCP Extensions for High Performance RFC 7323 The Addition of Explicit Congestion Notification (ECN) to IP RFC 3168 Robust Explicit Congestion Notification (ECN) Signaling with Nonces RFC 3540 IP Authentication Header RFC 4302 Mobility Support in IPv6 RFC 6275 Host Identity Protocol Version 2 (HIPv2) RFC 7401 Shim6: Level 3 Multihoming Shim Protocol for IPv6 RFC 5533 Computing the Internet Checksum RFC 1071 Internet Control Message Protocol RFC 792 IANA Internet Control Message Protocol (ICMP) Parameters checksum Helpers for calculating checksums.

defrag std Module containing helpers to re-assemble fragmented packets (contains allocations).

err Module containing error types that can be triggered.

ether_type Constants for the ethertype values for easy importing (e.g. use ether_type::*;).

icmpv4 Module containing ICMPv4 related types and constants.

icmpv6 Module containing ICMPv6 related types and constants io std ip_number Constants for the ip protocol numbers for easy importing (e.g. use ip_number::*;).

tcp_option Module containing the constants for tcp options (id number & sizes).

ArpEthIpv4Packet An ethernet & IPv4 “Address Resolution Protocol” Packet (a specific version of crate::ArpPacket).

ArpHardwareId Represents an ARP protocol hardware identifier.

ArpOperation Operation field value in an ARP packet.

Requirements for Internet Hosts – Communication Layers RFC 1122 Requirements for IP Version 4 Routers RFC 1812 Internet Control Message Protocol (ICMPv6) for the Internet Protocol Version 6 (IPv6) Specification RFC 4443 ICMP Router Discovery Messages RFC 1256 Internet Control Message Protocol version 6 (ICMPv6) Parameters Multicast Listener Discovery (MLD) for IPv6 RFC 2710 Neighbor Discovery for IP version 6 (IPv6) RFC 4861 LINKTYPE_LINUX_SLL on tcpdump LINUX_SLL header definition on libpcap Linux packet types definitions on the Linux kernel Address Resolution Protocol (ARP) Parameters Harware Types Arp hardware identifiers definitions on the Linux kernel “IEEE Standard for Local and metropolitan area networks-Media Access Control (MAC) Security,” in IEEE Std 802.1AE-2018 (Revision of IEEE Std 802.1AE-2006) , vol., no., pp.1-239, 26 Dec. 2018, doi: 10.1109/IEEESTD.2018.8585421.

“IEEE Standard for Local and metropolitan area networks–Media Access Control (MAC) Security Corrigendum 1: Tag Control Information Figure,” in IEEE Std 802.1AE-2018/Cor 1-2020 (Corrigendum to IEEE Std 802.1AE-2018) , vol., no., pp.1-14, 21 July 2020, doi: 10.1109/IEEESTD.2020.9144679.

ArpPacket “Address Resolution Protocol” Packet.
