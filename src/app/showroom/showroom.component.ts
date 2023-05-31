import {Component, EventEmitter, Input, OnChanges, OnDestroy, OnInit, Output, SimpleChanges} from '@angular/core';
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

  @Input() show_title:boolean=false;
  @Input() exclude_collections:string[]=[];
  @Input() collection_network:string="elrond-devnet";


  @Input() delay:number=0.5;
  @Input() size:string="300px";
  @Input() border="white solid 6px"
  @Output('update') onchange: EventEmitter<NFT>=new EventEmitter();


  private hInterval: any
  image_to_show: string | undefined;
  title: string="";
  transition: any={};



  constructor(public network:NetworkService) { }


  show_nft(nft:NFT){
    this.transition={transition: "opacity 0.3s ease-in-out",opacity:0}
    setTimeout(()=>{
      this.image_to_show=nft.visual;
      this.transition={transition: "opacity 0.3s ease-out-in",opacity:1}
      this.title=nft.name;
      this.onchange.emit(nft)
    },300);
  }

  select_nft(){
    if(this.nfts.length>0){
      const index=Math.round(Math.random()*(this.nfts.length-1));
      let nft=this.nfts[index];
      if(nft.visual.length>0 && (!nft.collection || this.exclude_collections.indexOf(nft.collection.id)==-1)){
        this.show_nft(this.nfts[index])
      }
    }
  }

  ngOnInit(): void {

    this.refresh();
  }

  refresh(){
    if(this.nfts.length>0){
      if(!this.hInterval) {
        this.select_nft();
        this.hInterval = setInterval(() => {
          this.select_nft();
        }, this.delay * 1000);
      }
    } else {
      clearInterval(this.hInterval)
    }



  }

  ngOnDestroy(): void {
    if(this.hInterval)clearInterval(this.hInterval);
  }

  // ngOnChanges(changes: SimpleChanges): void {
  //   if(this.operation_id!=""){
  //     this.network.get_nfts_from_operation(this.operation_id).subscribe((result)=>{
  //       this.nfts=result.nfts;
  //     })
  //   } else {
  //     if(this.collection_id!=""){
  //       this.network.get_nfts_from_collection(this.collection_id,this.collection_network).subscribe((result)=>{
  //         this.nfts=result.nfts;
  //       })
  //     }
  //   }
  // }

}
