import {Component, Input, OnDestroy, OnInit} from '@angular/core';
import {NFT} from "../../nft";
import {Collection} from "../../operation";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-showroom',
  templateUrl: './showroom.component.html',
  styleUrls: ['./showroom.component.css']
})
export class ShowroomComponent implements OnInit,OnDestroy {

  @Input() nfts:NFT[]=[];
  @Input() collections:Collection[]=[];
  @Input() operation_id:string="";
  @Input() delay:number=0.5;
  @Input() size:string="300px";

  private hInterval: NodeJS.Timeout | undefined;
  image_to_show: string | undefined;


  constructor(public network:NetworkService) { }

  ngOnInit(): void {
    this.hInterval=setInterval(()=>{
      if(this.nfts.length>0){
        const index=Math.round(Math.random()*this.nfts.length);
        this.image_to_show=this.nfts[index].visual;
      }
    },this.delay*1000);
    this.refresh();
  }

  refresh(){
    this.network.get_nfts_from_operation(this.operation_id).subscribe((result)=>{
      this.nfts=result.nfts;
    })
  }

  ngOnDestroy(): void {
    if(this.hInterval)clearInterval(this.hInterval);
  }

}
