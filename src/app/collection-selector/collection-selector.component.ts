import {Component, EventEmitter, Input, OnChanges, OnDestroy, Output, SimpleChanges} from '@angular/core';
import {$$, showError, showMessage} from "../../tools";
import {NetworkService} from "../network.service";
import {Collection} from "../../operation";
import {NFT} from "../../nft";
import {wait_message} from "../hourglass/hourglass.component";
import {MatSnackBar} from "@angular/material/snack-bar";

@Component({
  selector: 'app-collection-selector',
  templateUrl: './collection-selector.component.html',
  styleUrls: ['./collection-selector.component.css']
})
export class CollectionSelectorComponent implements OnChanges,OnDestroy {
  @Input("collection") sel_collection: Collection | undefined
  collections: Collection[] = []
  message = ""
  @Output("selected") onselect: EventEmitter<Collection> = new EventEmitter();
  @Output() endSearch: EventEmitter<Collection[]> = new EventEmitter();
  @Input() owner = ""
  @Input("create_collection") miner_or_validator:any
  @Input() network = ""
  @Input() roles = "canTransfer"
  @Input() limit = 300
  @Input() refresh_delay = 0
  @Input() color = "white"
  @Input() w_image = "200px"
  @Input() min_supply = 1
  @Input() animation = "crossfade"
  @Input("query") query_collection = "";
  @Input() title = "Sélectionnez une collection";

  handle: any = 0;
  nfts: NFT[] = [];
  delay_showroom=1;
  background:string=""

  constructor(public api: NetworkService,
              public toast: MatSnackBar) {
  }

  find_visual(col: Collection) {
    this.api.get_nfts_from_collection(col.id, this.network, this.min_supply, false).subscribe({
      next: (result: any) => {
        if (result.nfts && result.nfts.length >= this.min_supply) {
          col.cover = result.nfts[0].visual
        } else {
          col.cover = "" //provoque la disparition du NFT
        }
      },
      error: (err) => {
        showError(this, err)
      }
    })
  }


  refresh_collections(){
    if (this.owner) {
      this.api.get_collections(this.owner, this.network, true, this.limit, this.roles).subscribe((r: any) => {
        this.message = ""
        this.collections = []
        for (let col of r) {
          col.label = col.name
          if (col.roles) {
            for (let r of col.roles) {
              delete r.roles
            }
            this.collections.push(col)
          }
          if (this.w_image != '') this.find_visual(col);
        }
        if (this.collections.length == 0) showMessage(this, "Aucune collection pour cet utilisateur")
        if (this.collections.length == 1) {
          this.sel_collection = this.collections[0]
        }
      }, (error: any) => {
        this.api.wait()
        showError(this, error)
      })
    }
  }

  refresh() {
    if (this.handle != 0) {
      $$("Arret de la récupératon")
      clearInterval(this.handle)
      this.handle = 0
    }else{
      this.refresh_collections()
      $$("Mise en place d'une collecte des NFT toutes les " + this.refresh_delay + " secondes")
      if(this.refresh_delay>0){
        this.handle = setInterval(() => {this.refresh_collections()}, this.refresh_delay * 1000);
      }
    }



  }

  ngOnDestroy() {
    if (this.handle != 0) clearInterval(this.handle)
    this.reset();
  }

  ngOnChanges(changes: SimpleChanges): void {
    setTimeout(()=>{this.refresh()},500)
  }


  select_collection(c: any) {
    this.sel_collection = c
    this.onselect.emit(this.sel_collection);
    wait_message(this,"Chargement des visuels")
    this.api.get_nfts_from_collection(c.id, this.network, 20, false).subscribe({
      next: (r: any) => {
        this.nfts = r.nfts
        wait_message(this)
      },
      error: (err: any) => {
        showError(this, err)
        wait_message(this)
      }
    })
  }


  run_query($event: any, limit = 300) {
    if (!this.query_collection || this.query_collection == "") {
      this.collections = [];
      return;
    }
    wait_message(this, "Recherche des collections contenant '" + this.query_collection + "' dans le nom")

    this.api.get_collections(this.query_collection, this.network, false, limit, this.roles).subscribe({
      next: (cols) => {
        this.collections = cols;
        this.endSearch.emit(cols)
        for (let c of cols) {
          this.find_visual(c);
        }

        if (cols.length == 0) {
          showMessage(this, "Aucune collection pour cette recherche " + this.query_collection)
        } else {
          showMessage(this, this.query_collection.length + " collections trouvées")
        }
        if (cols.length == limit) showMessage(this, "Il manque probablement des réponses")
        wait_message(this)
        this.query_collection = ""
        if (cols.length == 1 && !this.miner_or_validator) this.select_collection(cols[0])
      }
    }
    )
  }


  open_gallery() {
    open(this.api.getExplorer("",this.network),"gallery")
  }

  reset() {
    this.query_collection="";
    this.refresh_delay=0;
    this.delay_showroom=0;
    this.collections=[];
    this.sel_collection=undefined
  }


  create_collection() {
    showMessage(this,"Fonctionnalité en cours de construction. Pour l'instant utiliser le web wallet")
  }
}
