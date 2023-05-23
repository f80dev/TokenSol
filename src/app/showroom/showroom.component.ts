import {Component, EventEmitter, Input, OnDestroy, OnInit, Output} from '@angular/core';
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
  @Input() collection_id:string="";
  @Input() show_title:boolean=false;

  @Input() collection_network:string="elrond-devnet";
  @Input() operation_id:string="";
  @Input() delay:number=0.5;
  @Input() size:string="300px";
  @Output('update') onchange: EventEmitter<NFT>=new EventEmitter();


  private hInterval: NodeJS.Timeout | undefined;
  image_to_show: string | undefined;
  title: string="";


  constructor(public network:NetworkService) { }

  ngOnInit(): void {
    this.hInterval=setInterval(()=>{
      if(this.nfts.length>0){
        const index=Math.round(Math.random()*(this.nfts.length-1));
        if(this.nfts[index].visual.length>0){
          this.image_to_show=this.nfts[index].visual;
          this.title=this.nfts[index].name;
          this.onchange.emit(this.nfts[index])
        }
      }
    },this.delay*1000);
    this.refresh();
  }

  refresh(){

    if(this.operation_id!=""){
      this.network.get_nfts_from_operation(this.operation_id).subscribe((result)=>{
        this.nfts=result.nfts;
      })
    } else {
      if(this.collection_id!=""){
        this.network.get_nfts_from_collection(this.collection_id,this.collection_network).subscribe((result)=>{
          this.nfts=result.nfts;
        })
      }
    }
  }

  ngOnDestroy(): void {
    if(this.hInterval)clearInterval(this.hInterval);
  }

}
