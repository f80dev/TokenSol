import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CollectionsComponent } from './collections.component';
import {ActivatedRoute} from "@angular/router";
import {HttpClientModule} from "@angular/common/http";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {RouterTestingModule} from "@angular/router/testing";
import {AliasPipe} from "../alias.pipe";

describe('CollectionsComponent', () => {
  let component: CollectionsComponent;
  let fixture: ComponentFixture<CollectionsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CollectionsComponent ,AliasPipe],
      imports: [HttpClientModule,MatSnackBarModule,RouterTestingModule],
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

  it("recupérer des collections",()=>{
    component.refresh();
    expect()
  })

});
