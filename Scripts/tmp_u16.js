const fs=require('fs'); const b=fs.readFileSync('D:/Unpack_3A/TLOU2/Assets/tlou2_assets/actor97/anim-ellie-player-movement.pak'); const base=9809440;
for(let o=0x120;o<0x200;o+=2){let u=b.readUInt16LE(base+o); console.log('0x'+o.toString(16).padStart(3,'0'),'u16',u.toString(16).padStart(4,'0'),'dec',u)}
