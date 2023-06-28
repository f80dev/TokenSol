import {Component, OnInit} from '@angular/core';
import {UserService} from "../user.service";
import {apply_params} from "../../tools";
import {environment} from "../../environments/environment";

@Component({
  selector: 'app-raffle',
  templateUrl: './raffle.component.html',
  styleUrls: ['./raffle.component.css']
})
export class RaffleComponent implements OnInit {
    selected_token: any;
    network: string=""

    constructor(public user:UserService) {
        this.user.params_available.subscribe({
            next:()=>{
                apply_params(this,this.user.params,environment)
            }
        })
    }

    ngOnInit(): void {

    }

}
