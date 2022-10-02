import { ComponentFixture, TestBed } from '@angular/core/testing';

import { KeysComponent } from './keys.component';
import {HttpClientModule} from "@angular/common/http";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {RouterTestingModule} from "@angular/router/testing";
import {MatDialogModule} from "@angular/material/dialog";

describe('KeysComponent', () => {
  let component: KeysComponent;
  let fixture: ComponentFixture<KeysComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ KeysComponent ],
      imports: [HttpClientModule,MatSnackBarModule,RouterTestingModule,MatDialogModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(KeysComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
