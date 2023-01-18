import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CollectionsComponent } from './collections.component';
import {ActivatedRoute} from "@angular/router";
import {HttpClientModule} from "@angular/common/http";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {RouterTestingModule} from "@angular/router/testing";
import {AliasPipe} from "../alias.pipe";
import {BrowserAnimationsModule} from "@angular/platform-browser/animations";

describe('CollectionsComponent', () => {
  let component: CollectionsComponent;
  let fixture: ComponentFixture<CollectionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CollectionsComponent ,AliasPipe],
      imports: [HttpClientModule,MatSnackBarModule,RouterTestingModule,BrowserAnimationsModule],
      providers: [{provide:AliasPipe}]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CollectionsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it("Création de collection",async()=>{
    component.network.get_collections("paul").subscribe((r:any)=>{
      if(r.length==0){
        component.new_collection.name="coltext";
        component.create_collection();
      }else{
        expect(r.length).toEqual(15)
      }
    })
  })

});
