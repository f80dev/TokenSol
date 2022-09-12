import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {showMessage} from "../../tools";

@Component({
  selector: 'app-authent',
  templateUrl: './authent.component.html',
  styleUrls: ['./authent.component.css']
})
export class AuthentComponent implements OnInit {

  @Input() intro_message:string="Email / Adresse de blockchaine";
  @Input() explain_message:string="Adresse de votre wallet ou votre email si vous n'en avez pas encore";
  @Output('authent') onauthent: EventEmitter<any>=new EventEmitter();
  @Output('cancel') oncancel: EventEmitter<any>=new EventEmitter();

  address: string="";


  constructor(
    public network:NetworkService,
    public userService:UserService
  ) { }

  ngOnInit(): void {
  }

  open_wallet(network: string) {
    this.userService.connect("",network).then((r:any)=>{
      this.address=r.address;
      this.onauthent.emit(this.address);
    })
  }


  validate() {
    if(this.address.indexOf("@")==-1 || !this.network.isElrond(this.address)){
      showMessage(this,"Le service n'est compatible qu'avec les adresses elrond");
    } else {
      this.onauthent.emit(this.address);
    }
  }

  update_address() {
    //this.address=this.address.replace("@gmail","@gmail.com");
  }
}
