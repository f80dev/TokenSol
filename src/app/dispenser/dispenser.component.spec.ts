import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DispenserComponent } from './dispenser.component';
import {HttpClientModule} from "@angular/common/http";
import {RouterTestingModule} from "@angular/router/testing";
import {MatDialogModule} from "@angular/material/dialog";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";

describe('DispenserComponent', () => {
  let component: DispenserComponent;
  let fixture: ComponentFixture<DispenserComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DispenserComponent ],
      imports: [HttpClientModule,RouterTestingModule,MatDialogModule,MatSnackBarModule],
      providers: [AliasPipe]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DispenserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
